import random, datetime
import uuid
from src.logger import logger
from src.schema.post import Post
from src.schema.user import User
import json
import pandas as pd
from langchain_core.runnables import RunnableSerializable
from langchain.schema import BaseMessage
from src.utils.rate_limit import RateLimiter
from collections import defaultdict
from typing import Any, List, Tuple

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

"""
For User posts
get all job-ids(set) (dummy collection)
after inserting post and user, add job id also in another collection
update the job id to the set
"""

def generate_new_user_id(user_ids: set, user_type: str, company_user_cnt_map: dict[str, int]=None, 
                         user_list_by_company: defaultdict[str, List[str]]=None, company=None) -> uuid.UUID:
    user_uuid = None
    if user_type == 'recruiter':
        num_recruiters = company_user_cnt_map[company] if company in company_user_cnt_map else 0
        if num_recruiters == len(user_list_by_company[company]):
            user_id_str = random.choice(user_list_by_company[company]) if company in user_list_by_company else None
            if user_id_str:
                user_uuid = uuid.UUID(user_id_str)
                

    if user_type == 'user' or not user_uuid:
        while True:
            user_uuid = uuid.uuid1()
            if str(user_uuid) not in user_ids:
                break
        if not user_uuid:
            raise ValueError("Invalid user_id: ", user_uuid)
    
    return user_uuid
        
        

def post_generation(user_type: str, post_chain: RunnableSerializable[dict, BaseMessage], 
                    user_chain: RunnableSerializable[dict, BaseMessage], user_format_instructions:str, post_format_instructions:str, 
                    rate_limiter: RateLimiter, user_ids:set, post_ids:set, job_id, job_title, company=None, description=None,
                    company_user_cnt_map: dict[str, int]=None, user_list_by_company: defaultdict[str, List[str]]=None)->Tuple[str, str]:

    if not rate_limiter.request():
        logger.info(f"Reached Open Router API limit")
        return None, None
        
    if user_type == 'user':
        post_content = post_chain.invoke({
            "position_role": job_title,
            "company_name": company,
            "format_instructions": post_format_instructions
        })
    else:
        post_content = post_chain.invoke({
            "job_title": job_title,
            "job_description": description,
            "format_instructions": post_format_instructions
        })

    logger.info(f"Generated post: \n {post_content.content}")
    logger.info(f"Generated {user_type} post content for {job_id} : {job_title}")

    if not rate_limiter.request():
        logger.info(f"Reached Open Router API limit")
        return None, None
    
    basic_user = user_chain.invoke({
        "format_instructions": user_format_instructions
    })

    user_details = json.loads(basic_user.model_dump_json())

    logger.info(f"Basic user details: {user_details}")

    user_uuid = generate_new_user_id(user_ids, user_type, company_user_cnt_map, user_list_by_company, company)
    timestamp = int(datetime.datetime.now().timestamp())
    valid_user = User(
        user_id=user_uuid,
        first_name=user_details['first_name'],
        last_name=user_details["last_name"],
        company=company,
        username="",
        createdAt=timestamp,
        updatedAt=timestamp,
        account_type=user_type
    )
    logger.info(f"Generated Valid user: {valid_user}")

    while True:
        post_uuid = uuid.uuid1()
        if str(post_uuid) not in post_ids:
            break
    if not post_uuid:
        raise ValueError("Invalid post_id: ", post_uuid)

    timestamp = int(datetime.datetime.now().timestamp())
    valid_post = Post(
        post_id = post_uuid,
        job_id=job_id,
        createdAt=timestamp,
        updatedAt=timestamp,
        author=str(user_uuid),
        content=str(post_content.content),
        ttl=0,  # Will be auto-calculated
        views=random.randint(0, 1000),
        comments=[],
        likes=[],
        repost={"timestamp": "", "count": 0},
    )

    if user_type == 'user':
        valid_post.job_id = ""
    logger.info(f"Post Object: \n {valid_post}")
    logger.info(f"Created post object for company: {company}")
    return valid_post.model_dump_json(), valid_user.model_dump_json()

