import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = os.getenv("API_GATEWAY_URL")
CAMERA_ID = "cam-01"

def upload_frame():
    # Get pre-generated S3 URL
    res = requests.post(API_ENDPOINT, json={"camera_id": CAMERA_ID}, timeout=5)
    res.raise_for_status()
    data = res.json()

    print(data)

def upload():
    upload_frame()

upload()