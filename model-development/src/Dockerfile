FROM python:3.12-slim

WORKDIR /model-developmenr/src

COPY . .
COPY ../requirements.txt .

RUN sudo apt-get update

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD [ "python","main.py"]