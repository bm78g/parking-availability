import time
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

API_ENDPOINT = os.getenv("API_GATEWAY_URL")
CAMERA_ID = "cam-01"

def upload_frame(image_bytes):
    # Get pre-generated S3 URL
    res = requests.post(API_ENDPOINT, json={"camera_id": CAMERA_ID}, timeout=5)
    res.raise_for_status()
    data = res.json()

    upload_url = data["upload_url"]
    s3_key = data["key"]

    put_res = requests.put(
        upload_url,
        data=image_bytes,
        headers={"Content-Type": "image/jpeg"},
        timeout=10
    )
    put_res.raise_for_status()
    print(f"Successfully uploaded {s3_key}")

def upload():
    # Iterate through data folder to find most recent image
    # TODO: Delete old files once data folder goes over a certain number of files
    DATA_PATH = Path(__file__).resolve().parent.parent / "data"
    latest_file = max(
        (f for f in DATA_PATH.iterdir() if f.is_file()),
        key=lambda el: el.stat().st_mtime
    )
    IMG_PATH = DATA_PATH / latest_file

    try:
        with open(IMG_PATH, "rb") as img:
            upload_frame(img)
    except Exception as err:
        print(f"Failed upload: {err}")