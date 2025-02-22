from logger import logger
from src.utils.user_gen_helper import connect_to_db, create_company_user_map, get_llm_chain, get_request_limiter, read_input_file, user_recruiter_generation

if __name__ == '__main__':
    try:
        print("Started main")
        logger.info("Started main")
        df = read_input_file("")
        company_user_map = create_company_user_map(df)
        chain_type='user-recruiter-generation'
        user_type='recruiter'
        user_recruiter_generation(company_user_map, chain_type, user_type)
        print("Finished main")
    except Exception as e:
        print(f"Error in main: {e}")

    """
    1. Read input csv file.
    2. Filter csv file (filter by company list)
    3. Get list of unique companies
    4. Get the users(recruiters) for each company from DB

    5. For each row in csv file:
       - randomly pick a user 
       - generate llm response
       - save to DB
    """