import cv2
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

def capture_frame():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        sys.exit("Error: Could not open camera")
    else:
        for _ in range(5):
            camera.read()

        return_value, frame = camera.read()

        if return_value:
            store_path = Path("data/")
            store_path.mkdir(parents=True, exist_ok=True)

            filename = datetime.now(timezone.utc).strftime("%m%d-%Y-%H%M%S")
            cv2.imwrite(f"data/{filename}.jpg", frame)
        else:
            sys.exit("Error: Could not read frame from video")

    camera.release()

def main():
    try:
        while True:
            capture_frame()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting program...")

if __name__ == "__main__":
    main()