import os
import math
import json
from pathlib import Path
import numpy as np
import cv2
import boto3
from ultralytics import YOLO

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

CONFIG_TABLE_NAME = os.environ.get("CONFIG_TABLE_NAME")
TELEMETRY_TABLE_NAME = os.environ.get("TELEMETRY_TABLE_NAME")

config_table = dynamodb.Table(CONFIG_TABLE_NAME)
telemetry_table = dynamodb.Table(TELEMETRY_TABLE_NAME)

MODEL_PATH = "/var/task/weights/yolov8s-visdrone.pt"
model = YOLO(MODEL_PATH)
CLASSES = [3, 4, 5, 8, 9]

BOUNDS_CACHE = {}

########################################################
#                OJBECT-TO-SPOT MATCHING               #
########################################################

# I'm assuming that getting the lower center of a bound will
# roughly calculate where the car touches the ground.
# It doesn't work as well for a perfect top-down view, but
# probably more practical for a more slanted camera angle.

# The contact coords will then be linked to the nearest center.
# However, there will need to be measures to prevent an unparked
# car from being matched to a spot.

# Calculate a point horizontally center and slightly above lower bound
def get_contact_coords(coords):
    x_center = (coords[0] + coords[2]) / 2
    height = coords[3] - coords[1]
    y_low = coords[3] - (height * 0.25)
    return (round(x_center), round(y_low))

# Returns the id of the nearest spot
def match_vehicle(coords, spots):
    contact_pos = get_contact_coords(coords)
    min_disp = math.inf
    nearest_spot = None

    for spot in spots:
        x_diff = spot["center"][0] - contact_pos[0]
        y_diff = spot["center"][1] - contact_pos[1]
        disp = math.sqrt(math.pow(x_diff, 2) + math.pow(y_diff, 2))

        # Calculates average diagonal distance to compute max distance allowed
        avg_radius = 0
        for vertex in spot["vertices"]:
            x_diff_center = spot["center"][0] - vertex[0]
            y_diff_center = spot["center"][1] - vertex[1]
            radius = math.sqrt(math.pow(x_diff_center, 2) + math.pow(y_diff_center, 2))
            avg_radius += radius
        avg_radius /= 4

        if disp < min_disp and disp < avg_radius:
            min_disp = disp
            nearest_spot = spot["id"]

    return nearest_spot

# Returns a list of occupied spots by id
def match_vehicles(results, spots):
    occupied = []
    for result in results:
        for box in result.boxes:
            coords = box.xyxy[0].tolist()
            matched = match_vehicle(coords, spots)
            if matched is not None:
                occupied.append(matched)

    occupied = list(set(occupied))
    occupied.sort()
    return occupied

########################################################
#                   OCCUPANCY STORAGE                  #
########################################################

def build_occupancy_data(spots, occupied):
    data = []
    queue = occupied.copy()

    index = 0
    for spot in spots:
        is_occupied = False
        if len(queue) > 0 and index == queue[0]:
            is_occupied = True
            queue.pop(0)

        data.append({
            "id": spot["id"],
            "occupied": is_occupied
        })
        index += 1

    return data

def get_camera_spots(camera_id: str) -> list:
    if camera_id in BOUNDS_CACHE:
        return BOUNDS_CACHE[camera_id]

    response = config_table.get_item(Key={"camera_id": camera_id})
    spots = response.get("Item", {}).get("spots")

    if not spots:
        raise ValueError(f"No configuration found for camera: {camera_id}")

    BOUNDS_CACHE[camera_id] = spots
    return spots

def lambda_handler(event, context):
    detail = event.get("detail", {})
    camera_id = detail.get("camera_id")
    bucket_name = detail.get("bucket_name")
    s3_key = detail.get("s3_key")

    if not all([camera_id, bucket_name, s3_key]):
        raise ValueError(f"Missing required event parameters: {detail}")

    # Retrieve parking lot configuration
    spots = get_camera_spots(camera_id)

    # Read image from S3 into memory
    s3_response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    img_bytes = s3_response["Body"].read()
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError(f"Failed to decode image from s3://{bucket_name}/{s3_key}")

    # Get occupancy
    results = model.predict(img, classes=CLASSES, conf=0.4, verbose=False)
    occupied_ids = match_vehicles(results, spots)
    occupancy_list = build_occupancy_data(spots, occupied_ids)
    timestamp = Path(s3_key).stem

    # Save to DynamoDB
    telemetry_table.put_item(
        Item={
            "camera_id": camera_id,
            "timestamp": timestamp,
            "s3_key": s3_key,
            "total_spots": len(spots),
            "occupied_count": len(occupied_ids),
            "vacant_count": len(spots) - len(occupied_ids),
            "occupancies": occupancy_list,
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Processed successfully",
            "camera_id": camera_id,
            "occupied_count": len(occupied_ids)
        }),
    }