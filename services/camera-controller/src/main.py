import cv2
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from s3_upload import upload
from eventbridge_trigger import trigger_analysis

def capture_frame():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        sys.exit("Error: Could not open camera")
    else:
        for _ in range(5):
            camera.read()

        return_value, frame = camera.read()

        if return_value:
            filename = datetime.now(timezone.utc).strftime("%m%d-%Y-%H%M%S")
            DATA_DIR = Path(__file__).resolve().parent.parent / "data"
            print(f"{DATA_DIR}/{filename}.jpg")

            DATA_DIR.mkdir(parents=True, exist_ok=True)

            cv2.imwrite(f"{DATA_DIR}/{filename}.jpg", frame)
        else:
            sys.exit("Error: Could not read frame from video")

    camera.release()

def main():
    try:
        while True:
            capture_frame()
            upload()
            trigger_analysis()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting program...")

if __name__ == "__main__":
    main()