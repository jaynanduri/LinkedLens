from pydantic import BaseModel, Field, field_validator, ValidationInfo
# import time_uuid
# import uuid_utils as uuid
import uuid
import re

class User(BaseModel):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid1)
    # user_id: int = Field(..., gt=0, description="Unique numeric identifier starting from 1")
    first_name: str
    last_name: str
    company: str
    username: str
    account_type: str

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @field_validator("user_id", mode="before")
    def validate_user_id(cls, value, info: ValidationInfo):
        return uuid.uuid1()
        # return time_uuid.TimeUUID()
    
    @field_validator("account_type", mode="before")
    def validate_account_type(cls, value, info: ValidationInfo):
        valid_types = ["recruiter", "user"]
        if value not in valid_types:
            raise ValueError(f"Invalid account type: {value}.")
        return value
    
    @field_validator("username", mode="before")
    def validate_or_generate_username(cls, value, info: ValidationInfo):
        """Ensure username is in the format: 'f_lastname' or auto-generate."""
        first_name = info.data.get("first_name", "").strip().lower()
        last_name = info.data.get("last_name", "").strip().lower()
        
        if not first_name or not last_name:
            raise ValueError("First and last name must be provided to generate a username.")

        # Generate username if not provided
        username = f"{first_name[0]}_{last_name}"

        # Validate username format
        if not re.match(r"^[a-z0-9_]+$", username):
            raise ValueError(f"Invalid username format: {username}")

        return username