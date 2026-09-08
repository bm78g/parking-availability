import json
import boto3

events_client = boto3.client("events", region_name="us-east-1")

def trigger_analysis(camera_id: str, bucket_name: str, s3_key: str):
    response = events_client.put_events(
        Entries=[
            {
                "EventBusName": "camera-pipeline-bus",
                "Source": "camera.controller",
                "DetailType": "ImageUploadCompleted",
                "Detail": json.dumps({
                    "camera_id": camera_id,
                    "bucket_name": bucket_name,
                    "s3_key": s3_key,
                }),
            }
        ]
    )
    
    if response["FailedEntryCount"] > 0:
        print(f"Failed to put event: {response['Entries']}")
    else:
        print(f"Successfully triggered CV Lambda for {s3_key}")