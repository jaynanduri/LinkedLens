import pandas as pd
from src.utils.gen_helper import *
from collections import defaultdict
from google.cloud.firestore import DocumentSnapshot
from src.utils.gen_helper import read_input_file
from src.utils.post_gen import post_generation
import json
from typing import List, Tuple



def create_company_user_map(input_df: pd.DataFrame, column_name: str)-> dict[str,int]:
    try:
        company_dict = input_df[column_name].value_counts().to_dict()
        company_user_cnt_map = {k: (v if v == 1 else v // 2) for k, v in company_dict.items()}
        return company_user_cnt_map
    except Exception as e:
        raise RuntimeError(f"Error creating company user count map: {e}")


def prepare_recruiter_ids_by_company(recruiters: List[DocumentSnapshot]) -> defaultdict[str, List[str]]:
    """Groups recruiter user IDs by company from a list of recruiter documents."""
    try:
        company_user_dict = defaultdict(list)
        for doc in recruiters:
            doc_dict = doc.to_dict()
            company_name = doc_dict['company']
            user_id = doc_dict['user_id'] 
            
            if company_name and user_id:
                company_user_dict[company_name].append(user_id)

        logger.info(f"Unique companies of recruiters: {len(company_user_dict)}")
        return company_user_dict
    except Exception as e:
        raise RuntimeError(f"Failed to create recruiter ids by company : {e}")


def get_post_and_user_chain_type(user_type:str)->Tuple[str, str]:
    """Based on user-type return the post-chain and user-chain to be used"""
    if user_type == 'recruiter':
        return "recruiter-post", "basic-user-details"
    elif user_type == 'user':
        return "user-post-generation", "basic-user-details"
    else:
        raise ValueError(f"Invalid user type: {user_type}. Should be either recruiter or user!")


def create_posts(input_df: pd.DataFrame, db_client: FirestoreClient, 
                 user_ids: set, post_ids: set, job_ids:set, user_type: str, 
                 company_user_cnt_map: dict[str, int]=None, user_list_by_company: defaultdict[str, List[str]]=None)->None:

    try:
        post_chain_type, user_chain_type = get_post_and_user_chain_type(user_type)
        post_chain, post_format_instructions = get_llm_chain(post_chain_type)
        user_chain, user_format_instructions = get_llm_chain(user_chain_type)
        
        req_rate_limiter = get_request_limiter()
        logger.info(f"Rate Limiter: {req_rate_limiter.num_requests}")
        generated_post_count = 0
        for _, row in input_df.iterrows():
            job_id = row['job_id']
            if job_id in job_ids:
                logger.info(f"{user_type.capitalize()} Post already generated for the job_id {job_id}")
                continue
            
            job_title = row['title']
            job_description = ""
            company = row['company_name']
            if user_type == 'recruiter':
                job_description = row['description']
            
            logger.info(f"Generating {user_type.capitalize()} Post: JobId: {job_id}; Title: {job_title}; Company Name: {company}")
            

            post_data_json, user_data_json = post_generation(user_type, post_chain, user_chain, user_format_instructions, 
                                                             post_format_instructions, req_rate_limiter, user_ids, post_ids, 
                                                             job_id, job_title, company, job_description, company_user_cnt_map, 
                                                             user_list_by_company)
            if not post_data_json:
                raise RuntimeError(f"Failed to generate post")
            
            post_data = json.loads(post_data_json)
            user_data = json.loads(user_data_json)

            logger.info(f"\nPost Data: \n {post_data}")
            logger.info(f"\nUser Data: \n {user_data}")

            db_client.insert_entry('users', user_data, user_data['user_id'])
            logger.info(f"Inserted user data to DB for post with job_id: {job_id}")
            db_client.insert_entry('posts', post_data, post_data['post_id'])
            logger.info(f"Inserted Post data into DB for job_id: {job_id}")
            if user_type == 'user':
                db_client.insert_entry('userPostJobIds', {"job_id": job_id, "post_id": post_data['post_id']}, job_id)
            
            job_ids.add(job_id)
            logger.info(f"Added job id {job_id} for tracking")
            post_ids.add(post_data['post_id'])
            logger.info(f"Added post id {post_data['post_id']} for tracking")
            user_ids.add(user_data['user_id'])
            logger.info(f"Added user id {user_data['user_id']} for tracking")

            # update user_list_by_company and update company_user_cnt
            if user_type == 'recruiter':
                new_user_id = user_data['user_id']
                company = user_data['company']
                new_user = False if new_user_id in user_list_by_company[company] else True if company in user_list_by_company else True
                logger.info(f"Created new user : {new_user}")
                if new_user:
                    user_list_by_company[company].append(new_user_id)
                    logger.info(f"Updated the user id in user list by company")

                logger.info(f"Length of updated user_list company : {len(user_list_by_company)}")
            generated_post_count += 1
            logger.info(f"Posts generated so far: {generated_post_count}")
        
        logger.info(f"Total posts generated {generated_post_count}")
        

    except Exception as e:
        raise RuntimeError(f"Failed to create {user_type} posts : {e}")


# invoked by DAG
def generate_posts(bucket_filepath: str, column_names: List[str], filter: bool, num_rows: int, user_type: str)->None:
    input_df = read_input_file(bucket_filepath, column_names, filter, num_rows)
    logger.info(f"Number of jobs to generate post {len(input_df)}")
    # Get map of required recruiters per conpany
    db_client = connect_to_db()
    company_user_cnt_map = None
    user_list_by_company = None
    
    if user_type == 'recruiter':
        logger.info(f"Fetching existing Recruiters by company")
        company_user_cnt_map = create_company_user_map(input_df, 'company_name')
        logger.info(f"company user count map length : {len(company_user_cnt_map)}")
        # get existing recruiters by company
        recruiter_users = db_client.filter_docs_equal('users', 'account_type', user_type)
        user_list_by_company = prepare_recruiter_ids_by_company(recruiter_users)
        logger.info(f"Company Recruiter Ids: {len(user_list_by_company)}")

    # get existing post ids:
    curr_posts = db_client.get_all_docs("posts")
    post_ids = get_docs_list_by_field(curr_posts, 'post_id')
    logger.info(f"Existing post ids: {len(post_ids)}")

    # get all user-ids
    curr_users = db_client.get_all_docs("users")
    user_ids = get_docs_list_by_field(curr_users, 'user_id')
    logger.info(f"Existing user ids: {len(user_ids)}")

    # change based on post chain
    if user_type == 'recruiter':
        curr_posts = db_client.get_all_docs("posts")
    else:
        curr_posts = db_client.get_all_docs("userPostJobIds")
    
    job_ids = get_docs_list_by_field(curr_posts, 'job_id')
    

    logger.info(f"Job Ids: {len(job_ids)}")
    logger.info(f"User Ids: \n {len(user_ids)}")
    logger.info(f"Post Ids: \n {len(post_ids)}")
    
    create_posts(input_df, db_client, user_ids, post_ids, job_ids, user_type, company_user_cnt_map, user_list_by_company)





# def create_hiring_posts(post_df: pd.DataFrame, post_chain_type: str):
#     """Generates and inserts hiring posts into the database based on job listings."""
#     try:
        
#         post_chain = get_llm_chain(post_chain_type)

#         # company_map eith user count
        
#         # get all recruiter-type users
#         recruiter_users = db_client.filter_docs_equal('users', 'account_type', 'recruiter')
#         company_recruiter_ids = prepare_recruiter_ids_by_company(recruiter_users)
#         logger.info(f"Company Recruiter Ids: {len(company_recruiter_ids)}")

#         curr_posts = db_client.get_all_docs("posts")
#         job_ids = get_docs_list_by_field(curr_posts, 'job_id')
#         logger.info(f"Existing job ids: {len(job_ids)}")
#         post_ids = get_docs_list_by_field(curr_posts, 'post_id')
#         logger.info(f"Existing post ids: {len(post_ids)}")
        
#         for _, row in post_df.iterrows():
#             job_id = row['job_id']
#             logger.info(f"Initiate post generation for job id:{job_id}")
#             if job_id and job_id not in job_ids:
                
#                 company_name = row['company_name']
#                 job_title = row['title']
#                 job_description = row['description']
#                 logger.info(f'Generating post for job_id:{job_id}, company: {company_name}, title: {job_title}')
#                 # pick a author
#                 author_id = random.choice(company_recruiter_ids[company_name]) if company_name in company_recruiter_ids else None
#                 if not author_id:
#                     raise ValueError(f"No recruiter id found for the company: {company_name}. Generate atleast one user profile for the company.")
                
#                 logger.info(f"Row Data: Job id: {job_id}, company_name: {company_name}, job_title: {job_title}")
                
#                 logger.info("Validate Open Router request limit")
#                 allow_request = req_rate_limiter.request()
#                 if not allow_request:
#                     logger.warning("Daily Request limit for Open Router API reached. Exiting...")
#                     break

#                 post_data_json = generate_recruiter_post(job_title, job_description, author_id, job_id, post_chain, post_ids)
#                 logger.info(f"Post data Json : \n\n {post_data_json}")
#                 post_data = json.loads(post_data_json)
#                 post_data['vectorized'] = False
#                 logger.info(f"Post content: \n{post_data['content']}")
#                 db_client.insert_entry('posts', post_data, post_data['post_id'])

#     except Exception as e:
#         raise RuntimeError(f"Failed to create hiring posts : {e}")
    
"""
Recruiter post
manage api limits
1. Prepare Company_map with required user count.
2. Prepare company map with existing user ids(recruiter) per company
3. Modify basic user prompt to include existing "first last name"/try to generate unique name each time.
4. get llm and chain - 2 post and user, all post ids and user ids set uuid only

5. for each row of input df:
        use title and description - invoke chain get post content
        generate post-ids - check against DB ids<-
        check company-user map to see if we have reached the limit for the company
        if yes - pick a random user from the list
        else:
            invoke basic user chain - get first and last name
            # for users remove default uuid generation*
            # add vectorized* to user and post*
            generate uuid and account type = recruiter
            validate user
        validate post
        return valid post and user
    add generated postid and user id in existing postids and user ids and in user ids in company map

"""

# def create_interview_exp_posts(input_df, post_chain_type, user_chain_type):
#     """Generates and inserts interview experience posts along with user profiles into the database."""
#     try:
#         # input_df with company name and title
#         req_rate_limiter = get_request_limiter()
#         db_client = connect_to_db()
#         # existing posts generated for these job-ids
#         curr_exp_posts = db_client.get_all_docs("userPostJobIds")
#         job_ids = get_docs_list_by_field(curr_exp_posts, 'job_id')
#         # get post chain
#         post_chain = get_llm_chain(post_chain_type)
#         # get user_chain and format instructions
#         user_chain, user_format_instructions = get_llm_chain(user_chain_type)

#         # get existing post ids:
#         curr_posts = db_client.get_all_docs("posts")
#         post_ids = get_docs_list_by_field(curr_posts, 'post_id')
#         logger.info(f"Existing post ids: {len(post_ids)}")

#         # get all user-ids
#         curr_users = db_client.get_all_docs("users")
#         user_ids = get_docs_list_by_field(curr_users, 'user_id')
#         logger.info(f"Existing user ids: {len(user_ids)}")

#         logger.info(f"User Ids: \n {user_ids}")
#         logger.info(f"Post Ids: \n {post_ids}")

#         for i, row in input_df.iterrows():
#             job_id = row['job_id']
#             if job_id in job_ids:
#                 logger.info(f"Interview experience user post already generated for the job_id {row['job_id']}")
#                 continue
#             logger.info(f"Generating post : {i+1}, JobId: {job_id}; Company: {row['company_name']}; Title: {row['title']}")
#             post_data_json, user_data_json = generate_interview_exp_post(user_ids, row['company_name'], row['title'], post_ids, post_chain, user_chain, user_format_instructions, req_rate_limiter)
#             if not post_data_json:
#                 raise RuntimeError(f"Failed to generate post")

#             post_data = json.loads(post_data_json)
#             user_data = json.loads(user_data_json)

#             logger.info(f"\nPost Data: \n {post_data}")
#             logger.info(f"\nUser Data: \n {user_data}")

#             db_client.insert_entry('users', user_data, user_data['user_id'])
#             logger.info(f"Inserted user data to DB for post: {i+1}")
#             db_client.insert_entry('posts', post_data, post_data['post_id'])
#             logger.info(f"Inserted Post data into DB: {i+1}")
#             db_client.insert_entry('userPostJobIds', {"job_id": job_id}, 'job_id')
#             job_ids.add(job_id)
#             logger.info(f"Inserted job id {job_id} for tracking")
            
#     except Exception as e:
#         raise RuntimeError(f"Failed to create interview experience posts : {e}")

