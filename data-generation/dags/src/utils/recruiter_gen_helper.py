import time
import json
from pydantic import ValidationError
import uuid
from src.logger import logger
from src.utils.gen_helper import *


def generate_recruiter(company, num_users, seen_names, ids, chain, format_instructions, rate_limiter, user_type):

    """Generates a list of unique recruiter users for a company."""

    attempt = 0
    company_valid_users = []
    while len(company_valid_users) < num_users and attempt < 3:
        try:
            logger.info(f"Attempt {attempt}: Generating {num_users} users for {company}...")
            # generate response
            llm_input = {
                "company": company,
                "num_users": num_users,
                "format_instructions": format_instructions,
                "user_type": user_type,
                "existing_users": list(seen_names)
            }
            allow_request = rate_limiter.request()
            if not allow_request:
                # API limit reached for the day, save generated data
                return company_valid_users, seen_names, allow_request
            response = chain.invoke(llm_input)

            # validate count and users
            user_list = response.users
            
            for user in user_list:
                # set account _type
                user.account_type = user_type
                # check for company name
                if user.company != company:
                    raise ValidationError(f"Company name {user.company} does not match {company}")
                
                # check for unique names
                if user.full_name not in seen_names:
                    user_json = user.model_dump_json()
                    # print("User json:", user_json)
                    company_valid_users.append(json.loads(user_json))
                    # print(company_valid_users)
                    seen_names.add(user.full_name)
                
                    # check for unique ids
                    # print("Old user id:", user.user_id)
                    if user.user_id in ids:
                        while user.user_id in ids:
                            user.user_id = uuid.uuid1()
                    
                    ids.add(user.user_id)

            
            if len(company_valid_users) < num_users:
                attempt+=1
                num_users = num_users - len(company_valid_users)
                logger.warning(f"Failed to generate {num_users} users for {company}. Trying again...")

                    
        except Exception as e:
            logger.warning(f"Validation error on attempt {attempt}: {e}")
            attempt+=1
            time.sleep(1)
    return company_valid_users, seen_names, True


        
        

def generate_recruiter_for_companies(company_usr_map, seen_names, ids, chain, format_instructions, rate_limiter, user_type):
    """Generates recruiter profiles for each company. """
    valid_users =[]

    try:
        for company, num_users in company_usr_map.items():
            logger.info(f"Generating {num_users} recruiters for {company}...")
            user, seen_names, allow_request = generate_recruiter(company, num_users, seen_names, ids, chain, format_instructions, rate_limiter, user_type)
            if len(user)> 0:
                logger.info(f"Generated {num_users} recruiters for {company} successfully.")
                valid_users.extend(user)
            else:
                logger.warning(f"Failed to generate {num_users} recruiters for {company}.")
            if not allow_request:
                logger.warning("Daily Request limit for Open Router API reached. Exiting...")
                return valid_users
        return valid_users
    except Exception as e:
        logger.error(f"Error generating users for companies: {e}")
        return valid_users


def fetch_existing_user_details(users, company_user_map):
    """Extracts existing user details and updates the company user map."""
    seen_names = set()
    ids = get_docs_list_by_field(users, 'user_id')
    for doc in users:
        user = doc.to_dict()
        full_name = user['first_name'] + " " + user['last_name']
        seen_names.add(full_name)

        company = user['company'].strip()
        if company in company_user_map:
            company_user_map[company] -= 1

            if company_user_map[company] == 0:
                del company_user_map[company]

    logger.info("Count of User IDS in DB: ", len(ids))
    logger.info("Companies to generated for: ", len(company_user_map))
    return seen_names, ids, company_user_map

def user_recruiter_generation(company_user_map, chain_type, user_type):
    """Generates and saves recruiter profile for companies. """
    try:
        req_rate_limiter = get_request_limiter()
        db_client = connect_to_db()
        chain, format_instructions = get_llm_chain(chain_type)
        
        while len(company_user_map)>0:
            curr_users = db_client.get_all_docs("users")
            seen_names, ids, company_user_map = fetch_existing_user_details(curr_users, company_user_map)
            if not req_rate_limiter.request():
                break
            valid_users = generate_recruiter_for_companies(company_user_map, seen_names, ids, chain, format_instructions, req_rate_limiter, user_type)
            if len(valid_users)==0:
                break
            # save to DB
            db_client.bulk_insert("users", valid_users, "user_id")
            logger.info(f"Saved {len(valid_users)} to DB")
        
        if len(company_user_map) == 0:
            logger.info("All Recruiter profile generation completed.")
        else:
            logger.info("Failed to generate some/all recruiter profiles")

    except Exception as e:
        raise RuntimeError(f"Error generating users : {e}")
 
    
def create_company_user_map(input_df, column_name):
    try:
        company_dict = input_df[column_name].value_counts().to_dict()
        company_user_map = {k: (v if v == 1 else v // 2) for k, v in company_dict.items()}
        return company_user_map
    except Exception as e:
        raise RuntimeError(f"Error creating company user map: {e}")
    

