from pydantic import BaseModel
from typing import List
from src.schema.user import User

class UserList(BaseModel):
    """Schema for response validation of List of users."""
    users: List[User]
