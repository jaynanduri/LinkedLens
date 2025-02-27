import random, datetime
import uuid
from src.logger import logger
from src.schema.post import Post
from src.schema.user import User
import json


def generate_recruiter_post(job_title: str, job_description: str, user_id: str, job_id: str, post_chain, post_ids):
    """
    Given a job title and description, generate a post for the recruiter using LLM.
    Args:
        job_title (str): The job title
        job_description (str): The job description
        user_id (str): The user id of the recruiter
    """
    
    post_content = post_chain.invoke({
    "job_title": job_title,
    "job_description": job_description
    })

    logger.info(f"Generated post content for {job_id} : {job_title}")

    while True:
        post_uuid = uuid.uuid1()
        if post_uuid not in post_ids:
            break
    if not post_uuid:
        raise ValueError("Invalid post_id: ", post_uuid)


    valid_post = Post(
        post_id = post_uuid,
        job_id=job_id,
        timestamp=int(datetime.datetime.now().timestamp()),
        author=user_id,
        content=post_content.content,
        ttl=0,  # Will be auto-calculated
        views=random.randint(0, 1000),
        comments=[],
        likes=[],
        repost={"timestamp": "", "count": 0},
    )
    logger.info(f"Created post object for job_id: {job_id}")

    # generate user profiles
    return valid_post.model_dump_json()


def generate_interview_exp_post(user_ids, post_ids, post_chain, user_chain, user_format_instructions, rate_limiter):

    if not rate_limiter.request():
        logger.info(f"Reached Open Router API limit")
        return None, None

    response = post_chain.invoke({

    })

    post_content = response.content
    company = response.company


    logger.info(f"Generated post content for {company}")

    if not rate_limiter.request():
        logger.info(f"Reached Open Router API limit")
        return None, None

    basic_user = user_chain.invoke({
        "format_instructions": user_format_instructions
    })

    user_details = json.loads(basic_user.model_dump_json())

    while True:
        post_uuid = uuid.uuid1()
        if post_uuid not in post_ids:
            break
    if not post_uuid:
        raise ValueError("Invalid post_id: ", post_uuid)

    
    valid_user = User(
        user_id="",
        first_name=user_details['first_name'],
        last_name=user_details["last_name"],
        company=company,
        username="",
        account_type="user"
    )

    while True:
        user_uuid = uuid.uuid1()
        if user_uuid not in user_ids:
            break
    if not user_uuid:
        raise ValueError("Invalid user_id: ", user_uuid)
    
    valid_user.user_id = user_uuid
    
    valid_post = Post(
        post_id = post_uuid,
        job_id="",
        timestamp=int(datetime.datetime.now().timestamp()),
        author=user_uuid,
        content=post_content.content,
        ttl=0,  # Will be auto-calculated
        views=random.randint(0, 1000),
        comments=[],
        likes=[],
        repost={"timestamp": "", "count": 0},
    )


    logger.info(f"Created post object for company: {company}")
    
    return valid_post.model_dump_json(), valid_user.model_dump_json()
