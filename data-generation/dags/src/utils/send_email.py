from src.config.config import settings
from email.mime.text import MIMEText
from jinja2 import Template  
from email.mime.multipart import MIMEMultipart
import smtplib


def send_success_email(**kwargs):
    subject_template = 'Airflow Success: {{ dag.dag_id }} - Data Generation tasks succeeded'
    body_template = '''Hi team,
    The Data Generation tasks in DAG {{ dag.dag_id }} succeeded.'''
    subject = Template(subject_template).render(dag=kwargs['dag'], task=kwargs['task'])
    body = Template(body_template).render(dag=kwargs['dag'], task=kwargs['task'])
    email_message = MIMEMultipart()
    email_message['Subject'] = subject
    email_message['From'] = settings.SMTP_EMAIL
    email_message.attach(MIMEText(body, 'plain'))
    send_email(email_message)

def send_failure_email(**kwargs):
    subject_template = 'Airflow Failed: {{ dag.dag_id }} - Data Generation tasks failed'
    body_template = '''Hi team,
    The Data Generation tasks in DAG {{ dag.dag_id }} failed.'''
    subject = Template(subject_template).render(dag=kwargs['dag'], task=kwargs['task'])
    body = Template(body_template).render(dag=kwargs['dag'], task=kwargs['task'])
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
        print("Successfully sent to all recipients: ", settings.SMTP_RECIPIENT_EMAILS)
        server.quit()
    except Exception as e:
        raise Exception(f"Email failed: {e}")