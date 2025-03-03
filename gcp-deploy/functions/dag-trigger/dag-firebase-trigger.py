import requests
import os
from cloudevents.http import CloudEvent
import functions_framework
from google.events.cloud import firestore

@functions_framework.cloud_event
def trigger_firestore(cloud_event: CloudEvent) -> None:
    """
    Triggers by a change to a Firestore document.

    Args:
        cloud_event: cloud event with information on the firestore event trigger
    """
    firestore_payload = firestore.DocumentEventData()
    response = make_airflow_request()
    if response is None:
        print(f"DAG not triggered successfully")
    else:
        print(f"DAG triggered successfully")

def make_airflow_request() -> requests.Response:

    #Hardcoded username and password
    username = os.getenv("AIRFLOW_USER","admin")
    password = os.getenv("AIRFLOW_PWD","admin")
    serverIP = os.getenv("SERVER_IP","0.0.0.0")
    dagName = os.getenv("DAG_NAME","testDag")

    #Airflow REST API endpoint for triggering DAG runs
    endpoint = f"api/v1/dags/{dagName}/dagRuns"
    url = f"http://{serverIP}:8080/{endpoint}"  #Replace with your Airflow server URL and port

    #Create a session with basic authentication
    session = requests.Session()
    session.auth = (username, password)

    try:
        response = session.post(url, json={}, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error triggering DAG: {e}")
        return None