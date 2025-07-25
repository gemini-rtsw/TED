#!/bin/python3
import requests
from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv
import os

load_dotenv('./../../.env')

# # Configuration
# GRAFANA_URL = "http://localhost:3001"  # Change to your Grafana URL
# API_ENDPOINT = f"{GRAFANA_URL}/api/teams"
# api_token = "admin"  # Replace with a valid admin API key

# Grafana credentials
username = "admin"
password = "softwareControl@TED"


def execPost(endpoint, payload, headers, auth):
    try:
        url = f"http://cpogea-lv3.cl.gemini.edu:3001/api{endpoint}"
        print(url)
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(username, password)
        ).json()
    except Exception as e:
        print(e)
        response = {}
    print(response)
    return response

#CREATE SERVICE ACCOUNT
service_acc_uid = execPost("/serviceaccounts",
        {
        "name": "auto_service_acc",
        "role": "Admin"
        },
        {
        "Content-Type": "application/json"
        },
        HTTPBasicAuth(username, password)
)['uid']

#CREATE API TOKEN
api_token = execPost(f"/serviceaccounts/{service_acc_uid}/tokens",
        {
        "name": "auto_token",
        },
        {
        "Content-Type": "application/json"
        },
        HTTPBasicAuth(username, password)
)['key']
print(api_token)

#CREATE TEAM SOFTWARE
execPost(f"/teams",
        {
        "name": "software",
        "email": "ofugo95@gmail.com"
        },
        {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
        },
        HTTPBasicAuth(username, password)
)




