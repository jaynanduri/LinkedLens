from pydantic import BaseModel
from typing import List
from schema.user import User

class UserList(BaseModel):
    users: List[User]

    # @field_validator("users")
    # def ensure_unique_names(cls, users):
    #     """Ensures unique names **within the company** (not globally)."""
    #     seen_names: Set[str] = set()

    #     for user in users:
    #         if user.full_name in seen_names:
    #             raise ValueError(f"Duplicate name detected: {user.full_name} within the same company.")
    #         seen_names.add(user.full_name)

    #     return users