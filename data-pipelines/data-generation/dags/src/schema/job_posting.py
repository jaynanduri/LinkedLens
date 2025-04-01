import pandas as pd
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import re

class ExperienceLevel(str, Enum):
    """Enum representing different experience levels for job postings."""
    MID_SENIOR = "Mid-Senior level"
    ASSOCIATE = "Associate"
    ENTRY = "Entry level"
    DIRECTOR = "Director"
    INTERNSHIP = "Internship"
    EXECUTIVE = "Executive"

class PayPeriod(str, Enum):
    """Enum representing different pay periods for job compensation."""
    HOURLY = "HOURLY"
    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"

class CompensationType(str, Enum):
    """Enum representing different types of job compensation."""
    BASE_SALARY = "BASE_SALARY"

class Currency(str, Enum):
    """Enum representing supported currencies for job salaries."""
    USD = "USD"
    CAD = "CAD"
    BBD = "BBD"
    EUR = "EUR"
    GBP = "GBP"

class FormattedWorkType(str, Enum):
    """Enum representing different work types for job postings."""
    CONTRACT = "Contract"
    PART_TIME = "Part-Time"
    FULL_TIME = "Full-Time"
    VOLUNTEER = "Volunteer"
    INTERNSHIP = "Internship"
    TEMPORARY = "Temporary"
    OTHER = "Other"

class JobPosting(BaseModel):
    """
    Model representing a job posting with various attributes 
    including company details, salary, job type, and timestamps.
    """
    job_id: str = Field(...)
    company_id: str
    company_name: str
    title: str
    description: str
    skills_desc: Optional[str] = ""
    formatted_experience_level: Optional[ExperienceLevel] = None
    formatted_work_type: Optional[FormattedWorkType] = None
    remote_allowed: Optional[bool] = None
    location: Optional[str] = ""
    zip_code: Optional[str] = ""
    pay_period: Optional[PayPeriod] = None
    compensation_type: Optional[CompensationType] = None
    min_salary: Optional[float] = None
    med_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: Optional[Currency] = None
    normalized_salary: Optional[float] = None
    # remove old dates
    # original_listed_time: Optional[datetime] = None
    # listed_time: Optional[datetime] = None
    # expiry: Optional[datetime] = None
    # closed_time: Optional[datetime] = None
    job_posting_url: Optional[str] = ""
    application_url: Optional[str] = ""
    views: Optional[int] = None
    applies: Optional[int] = None
    createdAt: int = Field(...)
    updatedAt: int = Field(...)
    ttl: int = Field(...)
    vectorized: bool = False

    @field_validator("zip_code", mode="before")
    def validate_zip_code(cls, value):
        if pd.isna(value) or not value:
            return ""
        if isinstance(value, float):
            value = int(value)
        value = str(value).strip()
        if not re.match(r"^\d{4,5}(-\d{4})?$", value):
            raise ValueError(f"Invalid ZIP code: {value}")
        return value


    @field_validator("pay_period", "compensation_type", "currency", "formatted_experience_level", "formatted_work_type", mode="before")
    def validate_enum_fields(cls, value, info):
        if pd.isna(value) or not value or value == 'None' or value == 'NONE':
            return None
        value = str(value).strip()

        field_enum_map = {
            "pay_period": PayPeriod,
            "compensation_type": CompensationType,
            "currency": Currency,
            "formatted_experience_level": ExperienceLevel,
            "formatted_work_type": FormattedWorkType,
        }

        field_name = info.field_name
        # handling for formatted_work_type - convert to lowercase and match
        if field_name == "formatted_work_type":
            lowercase_value = value.lower()
            mapping = {
                "contract": "Contract",
                "part-time": "Part-Time",
                "full-time": "Full-Time",
                "volunteer": "Volunteer",
                "internship": "Internship",
                "temporary": "Temporary",
                "other": "Other"
            }
            if lowercase_value in mapping:
                return FormattedWorkType(mapping[lowercase_value])
            raise ValueError(f"Invalid value '{value}' for field '{field_name}'. Expected one of {list(mapping.values())}.")
        


        # Convert all other enums to uppercase for validation
        if field_name != 'formatted_experience_level':
            value = value.upper()

        if value in field_enum_map[field_name].__members__.values():
            return field_enum_map[field_name](value)

        raise ValueError(f"Invalid value '{value}' for field '{field_name}'. Expected one of {list(field_enum_map[field_name].__members__.values())}.")

    # Datetime Fields Validator - YYYY-MM-DD HH:mm:ss)
    # @field_validator("original_listed_time", "listed_time", "expiry", "closed_time", mode="before")
    # def validate_datetime_fields(cls, value):
    #     if pd.isna(value) or not value:
    #         return None
    #     if isinstance(value, datetime):
    #         return value
        
    #     value = str(value).strip()
    #     try:
    #         return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    #     except ValueError:
    #         raise ValueError(f"Invalid datetime format: {value}. Expected format: YYYY-MM-DD HH:mm:ss")

    @field_validator("job_id", "company_id", "company_name", "title", "description", 
                     "skills_desc", "location", "job_posting_url", "application_url",
                     mode="before")
    def clean_strings(cls, value):
        if pd.isna(value) or not value or str(value).lower() == "none" :
            return None
        return str(value).strip()

class JobPostingList(BaseModel):
    """Schema for validation of List of JobPostings."""
    jobs: List[JobPosting]