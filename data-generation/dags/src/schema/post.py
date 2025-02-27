import uuid
from pydantic import BaseModel, Field, ValidationInfo, field_validator
from typing import List
from datetime import datetime
import random
from enum import Enum

class Comment(BaseModel):
    user_id: str
    comment: str

class Repost(BaseModel):
    timestamp: int = Field(default=0)
    count: int = Field(default=0)
 
    @field_validator('timestamp', mode='before')
    @classmethod
    def enforce_empty_timestamp(cls, v):
        return 0
 
    @field_validator('count', mode='before')
    @classmethod
    def enforce_zero_count(cls, v):
        return 0

class ReactionType(str, Enum):
    like = "like"
    celebrate = "celebrate"
    support = "support"
    funny = "funny"
    love = "love"
    insightful = "insightful"
 
# Reaction model for items in the likes array.
class Reaction(BaseModel):
    user_id: str
    reaction_type: ReactionType
    created_at: int  # using datetime for the timestamp
 
 
    @field_validator('created_at', mode='before')
    @classmethod
    def validate_created_at(cls, v, info: ValidationInfo):
        post_timestamp = info.data.get("timestamp", 0)
        if v <= post_timestamp:
            return post_timestamp + random.randint(1, 3600)
        return v
    


# Main Post model.
class Post(BaseModel):
    post_id: uuid.UUID = Field(default_factory=uuid.uuid1)
    job_id: str = Field(...)
    timestamp: int = Field(...)
    author: str = Field(...)
    content: str = Field(...)
    ttl: int = Field(...)
    views: int = Field(..., ge=0, le=1000)
    likes: List[Reaction] = Field(default_factory=list, max_items=10)  # 0-10 reactions.
    comments: List[Comment] = Field(default_factory=list)
    repost: Repost = Field(default_factory=Repost)
 
    @field_validator('comments', mode='before')
    @classmethod
    def enforce_empty_comments(cls, v):
        return []
 
    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        start_date = datetime(2025, 2, 17).timestamp()  # Feb 17, 2025
        end_date = datetime(2025, 2, 25).timestamp()  # Feb 25, 2025
 
        if not (start_date <= v <= end_date):
            return random.randint(int(start_date), int(end_date))  # Pick a random valid timestamp
 
        return v
 
 
    @field_validator('ttl', mode='before')
    @classmethod
    def validate_ttl(cls, v, info: ValidationInfo):
        timestamp = info.data.get('timestamp')  # Correct way to access fields
        if timestamp!=0:
          expected_ttl = timestamp + 90 * 24 * 60 * 60
          return expected_ttl
 
    @field_validator('likes', mode='after')
    @classmethod
    def sort_likes(cls, v):
        return sorted(v, key=lambda reaction: reaction.created_at)

class LinkedInPost(BaseModel):
    content: str = Field(description="Engaging LinkedIn recruiter post content with proper formatting")