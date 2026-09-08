import json
import os
import time
import boto3
from botocore.config import Config

s3_client = boto3.client("s3", config=Config(signature_version="s3v4"))
BUCKET_NAME = os.environ["BUCKET_NAME"]

def main(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        camera_id = body.get("camera_id", "default-cam")
        
        timestamp = int(time.time() * 1000)
        object_key = f"raw/{camera_id}/{timestamp}.jpg"

        # Generate presigned URL for uploading image
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
                "ContentType": "image/jpeg",
            },
            ExpiresIn=60 # Seconds
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "upload_url": presigned_url,
                "key": object_key
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }