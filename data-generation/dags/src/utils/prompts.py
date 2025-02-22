PROMTPS = {
    # "user-generation": """ You are an AI that generates realistic and diverse recruiter profiles for a tech company.

    # Given a company name "{company}" and a number {num_users}, generate {num_users} unique recruiter profiles.
    
    # Ensure the following:
    # - Gender balance (equal male and female names).
    # - Ethnic diversity.
    # - No duplicate first and last name combinations.
    # - User IDs should be sequential from 1.
    
    # Return a JSON list strictly in the following format:
    
    # {format_instructions}"""

    "user-recruiter-generation": """You are an AI that generates realistic and diverse recruiter profiles for a tech company.

Given a company name "{company}" and a number {num_users}, generate {num_users} unique recruiter profiles.

Return a JSON list strictly in the following format:

{format_instructions}

Ensure the following:
- Gender balance (equal male and female names).
- Ethnic diversity.
- No duplicate first and last name combinations.
- Account type should be {user_type}.
- User IDs should be sequential from 1.
- The generated names (first and last) should not repeat any of the names **Previously Generated Names**.

**Previously Generated Names**: {existing_users}"""
}