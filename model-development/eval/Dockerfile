FROM python:3.12-slim

WORKDIR /app

# Copy only the required files
COPY __init__.py .
COPY evaluators.py .
COPY settings.py .
COPY langsmith_client.py .
COPY post_eval.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default run command
CMD ["python", "post_eval.py"]
