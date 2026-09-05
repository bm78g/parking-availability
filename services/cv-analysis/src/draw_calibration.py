from pathlib import Path
import json
import cv2
import sys
import numpy as np

########################################################
#                      RENDERING                       #
########################################################

def draw_bound(bound):
    # Draw center
    cv2.circle(img, center=bound["center"], radius=3, color=(0, 0, 255), thickness=-1)

    # Draw bounds
    print(bound["vertices"])
    pts = np.array(bound["vertices"], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 255, 255))

    cv2.imshow("redraw", img)

########################################################
#                    INITIALIZATION                    #
########################################################

# CHANGE HERE TO VIEW DIFFERENT FILES
img_name = "sample.jpg"
version = 0

bound_path = f"data/bounds/{Path(img_name).stem}/{version:04d}.json"
img_path = f"data/images/{img_name}"

img = cv2.imread(img_path)
if img is None:
    sys.exit("Image not found")

with open(bound_path, 'r') as file:
    bounds = json.load(file)

for bound in bounds:
    draw_bound(bound)

while True:
    key = cv2.waitKey(1) & 0xFF # Wait a millisecond for input
    if key == ord('s'):
        break