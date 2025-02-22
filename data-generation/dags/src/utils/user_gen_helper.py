from src.utils.prompts import PROMTPS
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from src.schema.user_list import UserList
from src.llm.llm_client import get_open_router_llm
import time
import json
from pydantic import ValidationError
import uuid
from src.utils.db import FirestoreClient
from src.utils.rate_limit import RateLimiter
from src.config.config import settings

def get_llm_chain(chain_type):
    # prompt, llm, parser
    try:
        messages = [
            ("system", PROMTPS[chain_type])
        ]
        prompt = ChatPromptTemplate.from_messages(messages)

        parser = PydanticOutputParser(pydantic_object=UserList)
        format_instructions = parser.get_format_instructions()
        print("\nFormat Instructions:\n", format_instructions)
        print("\n")
        llm = get_open_router_llm(chain_type)
        chain = prompt | llm | parser

        return chain, format_instructions
    except Exception as e:
        print(f"Error creating chain: {e}")


def generate_recruiter(company, num_users, seen_names, ids, chain, format_instructions, rate_limiter, user_type):
    attempt = 0
    company_valid_users = []
    while len(company_valid_users) < num_users and attempt < 3:
        try:
            print(f"Attempt {attempt}: Generating {num_users} users for {company}...")
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
                return company_valid_users, seen_names, allow_request
            response = chain.invoke(llm_input)
            # if successfully generated  - check if count and users are valid
            user_list = response.users
            # validate user is company is as provided and is the user names are unique
            for user in user_list:
                # set account _type
                user.account_type = user_type
                # check for company name
                if user.company != company:
                    raise ValidationError(f"Company name {user.company} does not match {company}")
                
                # check for unique names
                if user.full_name not in seen_names:
                    user_json = user.model_dump_json()
                    print("User json:", user_json)
                    company_valid_users.append(json.loads(user_json))
                    # company_valid_users.append(user_json)
                    print(company_valid_users)
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
                print(f"Failed to generate {num_users} users for {company}. Trying again...")

                    
        except Exception as e:
            print("\nIn validation error-------------------------------------------------\n")
            print(f"Validation error on attempt {attempt}: {e}")
            attempt+=1
            print("Attempt: ", attempt)
            time.sleep(1)
    print(company_valid_users)
    return company_valid_users, seen_names, True


        
        

def generate_recruiter_for_companies(company_usr_map, seen_names, ids, chain, format_instructions, rate_limiter, user_type):
    valid_users =[]
    # chain, format_instructions = llm_chain(chain_type)
    try:
        for company, num_users in company_usr_map.items():
            print(f"Generating {num_users} recruiters for {company}...")
            user, seen_names, allow_request = generate_recruiter(company, num_users, seen_names, ids, chain, format_instructions, rate_limiter, user_type)
            if len(user)> 0:
                print(f"Generated {num_users} recruiters for {company} successfully.")
                valid_users.extend(user)
            else:
                print(f"Failed to generate {num_users} recruiters for {company}.")
            if not allow_request:
                print("Request limit reached. Exiting...")
                return valid_users
        return valid_users
    except Exception as e:
        print(f"Error generating users for companies: {e}")
        raise RuntimeError(f"Error generating users for companies: {e}")


def fetch_existing_user_details(users, company_user_map):
    seen_names = set()
    ids = set()
    for doc in users:
        user = doc.to_dict()
        full_name = user['first_name'] + " " + user['last_name']
        seen_names.add(full_name)
        ids.add(user['user_id'])

        company = user['company']
        if company in company_user_map:
            company_user_map[company] -= 1

            if company_user_map[company] == 0:
                del company_user_map[company]
    return seen_names, ids, company_user_map

def user_recruiter_generation(company_user_map, chain_type, user_type):
    try:
        req_rate_limiter = get_request_limiter()
        db_client = connect_to_db()
        chain, format_instructions = get_llm_chain(chain_type)
        while len(company_user_map)>0:
            # get all users 
            curr_users = db_client.get_all_docs("users")
            # create sets and update map
            seen_names, ids, company_user_map = fetch_existing_user_details(curr_users, company_user_map)
            # generate users for companies
            valid_users = generate_recruiter_for_companies(company_user_map, seen_names, ids, chain, format_instructions, req_rate_limiter, user_type)
            if len(valid_users)==0:
                break
            # save to DB
            db_client.bulk_insert("users", valid_users, "user_id")
            print("Saved to DB")
        if len(company_user_map) == 0:
            print("All Users Generated Done")
        else:
            print("Failed to generate all users")
    except Exception as e:
        print(f"Error generating users : {e}")
        raise RuntimeError(f"Error generating users : {e}")
 
# timeout defaults to 5mins!
# track #of request in a day terminate program after 200 requests


"""
1. read csv file
2. create map
3. connect to DB and get existing user
4. using users and map, generate list of existing users
5. Using existing user and map generate new users
6. Save to DB
"""

def read_input_file(filepath):
    try:
        # read csv file
        return None
    except Exception as e:
        print(f"Error reading input file: {e}")
        raise RuntimeError(f"Error reading input file: {e}")
    
def create_company_user_map(input_df):
    try:
        # create map
        company_user_map = {
            "Microsoft": 2,
            "Google": 2,
            "Meta": 3,
            "Amazon": 3
        }
        return company_user_map
    except Exception as e:
        print(f"Error creating company user map: {e}")
        raise RuntimeError(f"Error creating company user map: {e}")
    
def connect_to_db():
    try:
        # connect to DB
        db_client = FirestoreClient()
        print("Connected to firestore")
        return db_client
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        raise RuntimeError(f"Error connecting to DB: {e}")
    
def get_request_limiter():
    try:
        request_limiter = RateLimiter(settings.MAX_OPEN_AI_REQUEST_PER_MIN, settings.MAX_OPEN_AI_REQUEST_PER_DAY)
        return request_limiter
    except Exception as e:
        print(f"Error creating request limiter: {e}")
        raise RuntimeError(f"Error creating request limiter: {e}")
