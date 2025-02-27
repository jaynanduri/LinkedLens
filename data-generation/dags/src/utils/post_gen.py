from utils.prompts import PROMTPS
from langchain.prompts import PromptTemplate
from schema.post import Post, ReactionType
from schema.user_list import UserList
from langchain.output_parsers import PydanticOutputParser
import logging
import random, datetime
from llm.llm_client import get_open_router_llm


logger = logging.getLogger(__name__)

def generate_recruiter_posts(job_title: str, job_description: str, user_id: str) -> tuple[Post, UserList]:
    """
    Given a job title and description, generate a post for the recruiter using LLM.
    Args:
        job_title (str): The job title
        job_description (str): The job description
        user_id (str): The user id of the recruiter
    Returns:
        Post: The generated post
    """
    llm = get_open_router_llm("recruiter_post")
    post_template = PromptTemplate.from_template(PROMTPS["recruiter_post"])
    chain = post_template | llm 
    post_content = chain.invoke({
    "job_title": job_title,
    "job_description": job_description
    })
    logger.info("Generated post content")
    # Create validated Post object
    valid_post = Post(
        job_id=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        timestamp=int(datetime.datetime.now().timestamp()),
        author=user_id,
        content=post_content.content,
        ttl=0,  # Will be auto-calculated
        views=random.randint(0, 1000),
        comments=[],
        likes=[{"user_id": datetime.datetime.now().strftime("%Y%m%d%H%M%S"), "reaction_type": random.choice(list(ReactionType)), "created_at": int(datetime.datetime.now().timestamp())} for _ in range(10)],
        repost={"timestamp": "", "count": 0},
    )
    logger.info("Created post object")
    user_template = PromptTemplate.from_template(PROMTPS["linkedin-user-profiles"])
    user_chain = user_template | llm
    user_ids = [reaction["user_id"] for reaction in valid_post.likes]
    parser = PydanticOutputParser(pydantic_object=UserList)
    format_instructions = parser.get_format_instructions()
    users = user_chain.invoke({
        "user_ids": user_ids,
        "format_instructions": format_instructions,
        "user_type": "user",
    })
    return valid_post, users
    