## OpenwebUI

![Demo](/images/Demo.gif)

We are using customized version of [OpenwebUI](https://github.com/open-webui/open-webui), open-source project for chat applications. The customization includes:
- **Main feed**: LinkedIn-like feed for displaying recent posts and job listings `src/routes/linkedin`.
- **Job Posting Page**: displaying job details, description, and a button to apply for the job `src/routes/jobs`.
- **User and Recruiter Post Pages**: displaying the user-generated content on the website `src/routes/posts`.
- **LinkedLens Agent Function**: calling our workflow endpoint, handling the user interaction, enforcing guardrails.

## Database

We utilize a **PostgreSQL** database to store application data. The primary tables relevant to the core *functionality*, *monitoring* and *evaluation*:

- **`chat`** table schema (truncated):
  - `id`: varchar(255)
  - `user_id`: varchar(255)
  - `title`: text
  - `created_at`: datetime
  - `chat`: json
  - ...

- **`feedback`** table schema (truncated):
  - `id`: text
  - `user_id`: text
  - `data`: json
  - `meta`: json
  - `snapshot`: json
  - `created_at`: datetime
  - ...
