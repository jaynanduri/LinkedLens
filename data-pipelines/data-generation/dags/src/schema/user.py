from pydantic import BaseModel, Field, field_validator, ValidationInfo
import uuid
import re

class BasicUser(BaseModel):
    first_name: str
    last_name: str

class User(BaseModel):
    """Schema for response validation of user data."""
    user_id: uuid.UUID = Field(default_factory=uuid.uuid1)
    first_name: str
    last_name: str
    company: str
    username: str
    account_type: str
    createdAt: int = Field(...)
    updatedAt: int = Field(...)
    vectorized: bool = False

    @property
    def full_name(self):
        """Returns the full name by combining first and last name."""
        return f"{self.first_name} {self.last_name}"
    
    
    @field_validator("account_type", mode="before")
    def validate_account_type(cls, value, info: ValidationInfo):
        """Validates that account_type is either 'recruiter' or 'user'."""
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
        clean_last = re.sub(r'[^a-zA-Z]', '', last_name)
        username = f"{first_name[0]}_{clean_last}"

        # Validate username format
        if not re.match(r"^[a-z0-9_]+$", username):
            raise ValueError(f"Invalid username format: {username}")

        return username