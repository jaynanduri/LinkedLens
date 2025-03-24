from src.config.config import settings
from email.mime.text import MIMEText
from jinja2 import Template  
from email.mime.multipart import MIMEMultipart
import smtplib
from src.logger import logger


def send_success_email(dag_id, task_id, execution_date):
    subject_template = 'Airflow Success: {{ dag_id }}'
    body_template = '''Hi team,
    The task {{ task_id }} in DAG {{ dag_id }} successfully executed at {{ execution_date }}.'''

    subject = Template(subject_template).render(dag_id=dag_id)
    body = Template(body_template).render(dag_id=dag_id, task_id=task_id, execution_date=execution_date)
    email_message = MIMEMultipart()
    email_message['Subject'] = subject
    email_message['From'] = settings.SMTP_EMAIL
    email_message.attach(MIMEText(body, 'plain'))
    send_email(email_message)

def send_failure_email(dag_id, task_id, log_url):
    subject_template = 'Airflow Failed: {{ dag_id }}'
    body_template = '''Hi team,
    The task {{ task_id }} in DAG {{ dag_id }} failed. Check the Log for more details:{{ log_url }}.'''
    subject = Template(subject_template).render(dag_id=dag_id)
    body = Template(body_template).render(dag_id=dag_id, task_id=task_id, log_url=log_url)
    email_message = MIMEMultipart()
    email_message['Subject'] = subject
    email_message['From'] = settings.SMTP_EMAIL
    email_message.attach(MIMEText(body, 'plain'))
    send_email(email_message)



def send_email(email_message):
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        recipients = [email.strip() for email in  settings.SMTP_RECIPIENT_EMAILS.split(',') if email.strip()]
        email_message['To'] = ', '.join(recipients)
        server.sendmail(settings.SMTP_EMAIL, recipients, email_message.as_string())
        logger.info(f"Successfully sent to all recipients: {settings.SMTP_RECIPIENT_EMAILS}")
        server.quit()
    except Exception as e:
        raise Exception(f"Email failed: {e}")