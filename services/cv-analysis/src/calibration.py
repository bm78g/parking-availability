import cv2
import sys
import json
import numpy as np
import math
from pathlib import Path

vertices = []
polygons = []

########################################################
#                   IMAGE ANNOTATION                   #
########################################################

def find_center(vertices):
    x_avg = y_avg = 0
    for vertex in vertices:
        x_avg += vertex[0]
        y_avg += vertex[1]
    x_avg /= 4
    y_avg /= 4
    center = (round(x_avg), round(y_avg))
    return center

def sort_vertices(center, vertices, polygons):
    angles = []
    for vertex in vertices:
        angle = math.atan2(vertex[1] - center[1], vertex[0] - center[0])
        angles.append(angle)

    # Sort vertices based on angle from center
    v_sorted = [x for _, x in sorted(zip(angles, vertices))]
    return v_sorted

def draw_bound(vertices, polygons):
    center = find_center(vertices)
    # Draw center for debug purposes
    cv2.circle(img, center=center, radius=3, color=(255, 0, 0), thickness=-1)

    # Vertices sorted to ensure shape is closed
    # Otherwise, bounds will be drawn in the order they were selected, often creating figure-8's
    v_sorted = sort_vertices(center, vertices, polygons)
    polygons.append(v_sorted.copy())

    pts = np.array(polygons[len(polygons) - 1], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 255, 255))

def click_event(event, x, y, flags, param):
    global vertices, polygons
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(img, center=(x, y), radius=3, color=(0, 0, 255), thickness=-1)
        vertices.append([x, y])

        # Draw polygon once enough vertices are selected
        if len(vertices) == 4:
            draw_bound(vertices, polygons)
            vertices = []

        cv2.imshow("display", img)

########################################################
#                     FILE STORAGE                     #
########################################################

def store_bounds():
    global polygons
    bounds = []
    
    count = 0
    for poly in polygons:
        bound = {
            "id": count,
            "vertices": poly,
            "center": find_center(poly)
        }
        bounds.append(bound)
        count += 1

    # Incremental versioning of bounds data to avoid destructive overwrites
    # It's especially critical for the calibration to be non-destructive,
    # as the process is fully manual while other processes are automatic and idempotent

    # Create directory
    filename_stem = Path(filename).stem
    bounds_dir = Path(f"data/bounds/{filename_stem}")
    bounds_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    while True:
        store_path = f"data/bounds/{filename_stem}/{count:04d}.json"
        store_path = Path(store_path)

        if store_path.is_file():
            count += 1
        else:
            with open(store_path, "w") as file:
                json.dump(bounds, file, indent=4)
            break

########################################################
#                    INITIALIZATION                    #
########################################################

path = "data/images/"
filename = "sample.jpg"
img = cv2.imread(path + filename)

if img is None:
    sys.exit("Image not found")

cv2.imshow("display", img)
cv2.setMouseCallback("display", click_event)

while True:
    key = cv2.waitKey(1) & 0xFF # Wait a millisecond for input
    if key == ord('s'):
        store_bounds()
        break

cv2.destroyAllWindows()