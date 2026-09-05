import cv2
from ultralytics import YOLO
import json
from pathlib import Path
import math

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

def get_contact_coords(coords):
    # Calculate a point horizontally center and slightly above lower bound
    x_center = (coords[0] + coords[2]) / 2

    height = coords[3] - coords[1]
    y_low = coords[3] - (height * 0.25)

    contact_coords = (round(x_center), round(y_low))

    cv2.circle(annotated_img, center=contact_coords, radius=3, color=(0, 0, 255), thickness=-1)

    return contact_coords

# Returns the id of the nearest spot
def match_vehicle(coords, spots):
    # Match to closest center for now
    # This does make matching an O(N^2) operation,
    # but the sample size is small enough for it to not be a problem
    contact_pos = get_contact_coords(coords)

    min_disp = math.inf
    nearest_spot = None
    for spot in spots:
        # Find centers and use Pythagorean theorem to find displacement
        x_diff = spot["center"][0] - contact_pos[0]
        y_diff = spot["center"][1] - contact_pos[1]
        disp = math.sqrt(math.pow(x_diff, 2) + math.pow(y_diff, 2))

        # Average diagonal radius for 4 points
        # Used as maximum distance allowed to be counted as occupying a spot
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
    # Extract coords and call match_vehicle
    occupied = []

    for result in results:
        for box in result.boxes:
            coords = box.xyxy[0].tolist()
            matched = match_vehicle(coords, spots)
            if matched != None:
                occupied.append(matched)

    occupied = list(set(occupied))
    return occupied

########################################################
#                   OCCUPANCY STORAGE                  #
########################################################

def store_occupancy(spots, occupied):
    data = []
    queue = occupied.copy()

    index = 0
    for spot in spots:
        occupied = False
        if index == queue[0]:
            occupied = True
            queue.pop(0)

        occupancy = {
            "id": spot["id"],
            "occupied": occupied
        }
        data.append(occupancy)

        index += 1

    datapath = Path(f"data/occupancies")
    datapath.mkdir(parents=True, exist_ok=True)
    
    with open(f"data/occupancies/{Path(filename).stem}.json", "w") as file:
        json.dump(data, file, indent=4)

def compute():
    occupied = match_vehicles(results, spots)
    store_occupancy(spots, occupied)

########################################################
#                    INITIALIZATION                    #
########################################################

model = YOLO("yolov8s-visdrone.pt")
CLASSES = [3, 4, 5, 8, 9]

# CHANGE THESE FOR DIFFERENT IMAGES AND VERSIONS
filename = "sample.jpg"
version = 0

bound_path = f"data/bounds/{Path(filename).stem}/{version:04d}.json"
img_path = f"data/images/{filename}"

with open("data/bounds/sample/0000.json") as file:
    spots = json.load(file)
img = cv2.imread(img_path)

# Display results for debug purposes
results = model.predict(img, classes=CLASSES, conf=0.4, verbose=False)

annotated_img = results[0].plot()

# UNCOMMENT FOR VISUAL DEBUG
# cv2.imshow("display", annotated_img)

# while True:
#     key = cv2.waitKey(1) & 0xFF
#     if key == ord('s'):
#         break