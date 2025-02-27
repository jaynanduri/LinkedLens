PROMTPS = {

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

    **Previously Generated Names**: {existing_users}""",

    "recruiter-post": """Create a LinkedIn recruiter post for a {job_title} position following this exact structure:

    🚀 We're Hiring: {job_title}!
    ✨ About the Role:
    - {{Insert 1-sentence company introduction}}
    - {{Share core team mission}}

    🔍 Key Responsibilities:
    {{
    - Extract 3-5 main responsibilities from job description
    - Focus on impact rather than tasks
    }}

    ✅ Ideal Candidate:
    {{
    - List 3-5 key requirements from job description
    - Include both hard and soft skills
    }}

    🌟 Why Join Us?
    {{{{
    - Highlight 2-3 unique benefits/opportunities
    - Keep it employee-centric
    }}}}

    📩 How to Apply:
    - Include clear call-to-action
    - Add relevant hashtags (3-5)

    Job Description Context: {job_description}

    Maintain these formatting rules:
    - Use emojis as section headers
    - Keep paragraphs under 3 lines
    - Use clean line breaks between sections
    - Avoid markdown formatting
    - Maintain corporate tone with personality""",

    "linkedin-user-profiles": """You are an AI that generates realistic and diverse user profiles linkedIn.

        Given a list user ids {user_ids}, generate a list of unique user profiles.

        Return a JSON list strictly in the following format:

        {format_instructions}

        Ensure the following:
        - Gender balance (equal male and female names).
        - Ethnic diversity.
        - No duplicate first and last name combinations.
        - Account type should be {user_type}.
        - User IDs should be sequential from 1.
        - The generated names (first and last) should not repeat any of the names"""
}