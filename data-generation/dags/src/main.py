from src.logger import logger
from src.utils.user_gen_helper import create_company_user_map, read_input_file, user_recruiter_generation

if __name__ == '__main__':
    try:
        logger.info("Start Recruiter profile generation.")
        df = read_input_file("")
        company_user_map = create_company_user_map(df)
        chain_type='user-recruiter-generation'
        user_type='recruiter'
        user_recruiter_generation(company_user_map, chain_type, user_type)
        logger.info("Completed Recruiter profile generation.")
    except Exception as e:
        print(f"Error in main: {e}")