import pandas as pd
from src.utils.gen_helper import *
from collections import defaultdict
import random
from src.utils.post_gen import generate_recruiter_post, generate_interview_exp_post
import json


def prepare_recruiter_ids_by_company(recruiters):
    try:
        company_user_dict = defaultdict(list)
        for doc in recruiters:
            doc_dict = doc.to_dict()
            company_name = doc_dict['company']
            user_id = doc_dict['user_id'] 
            
            if company_name and user_id:
                company_user_dict[company_name].append(user_id)

        logger.info(f"Unique companies of recruiters: {len(company_user_dict)}")
        return dict(company_user_dict)
    except Exception as e:
        raise RuntimeError(f"Failed to create recruiter ids by company : {e}")


def create_hiring_posts(post_df: pd.DataFrame, post_chain_type: str):
    try:
        req_rate_limiter = get_request_limiter()
        db_client = connect_to_db()
        post_chain = get_llm_chain(post_chain_type)
        
        # get all recruiter-type users
        recruiter_users = db_client.filter_docs_equal('users', 'account_type', 'recruiter')
        company_recruiter_ids = prepare_recruiter_ids_by_company(recruiter_users)
        logger.info(f"Company Recruiter Ids: {len(company_recruiter_ids)}")

        curr_posts = db_client.get_all_docs("posts")
        job_ids = get_docs_list_by_field(curr_posts, 'job_id')
        logger.info(f"Existing job ids: {len(job_ids)}")
        post_ids = get_docs_list_by_field(curr_posts, 'post_id')
        logger.info(f"Existing post ids: {len(post_ids)}")
        
        for _, row in post_df.iterrows():
            job_id = row['job_id']
            logger.info(f"Initiate post generation for job id:{job_id}")
            if job_id and job_id not in job_ids:
                
                company_name = row['company_name']
                job_title = row['title']
                job_description = row['description']
                logger.info(f'Generating post for job_id:{job_id}, company: {company_name}, title: {job_title}')
                # pick a author
                author_id = random.choice(company_recruiter_ids[company_name]) if company_name in company_recruiter_ids else None
                if not author_id:
                    raise ValueError(f"No recruiter id found for the company: {company_name}. Generate atleast one user profile for the company.")
                
                logger.info(f"Row Data: Job id: {job_id}, company_name: {company_name}, job_title: {job_title}")
                
                logger.info("Validate Open Router request limit")
                allow_request = req_rate_limiter.request()
                if not allow_request:
                    logger.warning("Daily Request limit for Open Router API reached. Exiting...")
                    break

                post_data_json = generate_recruiter_post(job_title, job_description, author_id, job_id, post_chain, post_ids)
                logger.info(f"Post data Json : \n\n {post_data_json}")
                post_data = json.loads(post_data_json)
                logger.info(f"Post content: \n{post_data['content']}")
                db_client.insert_entry('posts', post_data, post_data['post_id'])

    except Exception as e:
        raise RuntimeError(f"Failed to create hiring posts : {e}")
    

def create_interview_exp_posts(input_df, post_chain_type, user_chain_type):
    try:
        # input_df with company name and title
        req_rate_limiter = get_request_limiter()
        db_client = connect_to_db()
        # get post chain
        post_chain = get_llm_chain(post_chain_type)
        # get user_chain and format instructions
        user_chain, user_format_instructions = get_llm_chain(user_chain_type)

        # get existing post ids:
        curr_posts = db_client.get_all_docs("posts")
        post_ids = get_docs_list_by_field(curr_posts, 'post_id')
        logger.info(f"Existing post ids: {len(post_ids)}")

        # get all user-ids
        curr_users = db_client.get_all_docs("users")
        user_ids = get_docs_list_by_field(curr_users, 'user_id')
        logger.info(f"Existing user ids: {len(user_ids)}")

        logger.info(f"User Ids: \n {user_ids}")
        logger.info(f"Post Ids: \n {post_ids}")

        for i, row in input_df.iterrows():
            logger.info(f"Generating post : {i+1}, Company: {row['company_name']}; Title: {row['title']}")
            post_data_json, user_data_json = generate_interview_exp_post(user_ids, row['company_name'], row['title'], post_ids, post_chain, user_chain, user_format_instructions, req_rate_limiter)
            if not post_data_json:
                raise RuntimeError(f"Failed to generate post")
            print(f"Converting post to json: {post_data_json}")
            print(f"Converting user to json: {user_data_json}")
            post_data = json.loads(post_data_json)
            user_data = json.loads(user_data_json)
            
            logger.info(f"\nPost Data: \n {post_data}")
            logger.info(f"\nUser Data: \n {user_data}")

            db_client.insert_entry('users', user_data, user_data['user_id'])
            logger.info(f"Inserted user data to DB for post: {i+1}")
            db_client.insert_entry('posts', post_data, post_data['post_id'])
            logger.info(f"Inserted Post data into DB: {i+1}")


    except Exception as e:
        raise RuntimeError(f"Failed to create interview experience posts : {e}")

