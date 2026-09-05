# OpenCV Occupancy Identifier

## About
OpenCV Occupancy Identifier is an internal software component of
the Parking Occupancy Tracker project. It serves the critical purpose
of configuring the bounds of the parking spots, identifying the
locations of the detected vehicles, and comparing the spots to the
vehicles to approximate the occupancy of each spot.

The repository is comprised of three parts:
- Bound configuration
- Object identification
- Event API endpoint

## How it works
1. ```calibration.py``` retrieves the specified image file and opens
it in a window, allowing the user to select the regions of a parking
spot. Exiting the program by pressing 's' will save the currently
drawn polygons inside ```data/bounds/{image_name}/{version}.json```.
2. ```draw_calibration.py``` loads the bounds data created by the
user and redraws them in a window to be reviewed visually.
3. ```detect_object.py``` uses YOLOv8 to identify all vehicles in the
image, then compares their locations to the parking spots to get a
list of all occupancy statuses.
4. ```server.py``` exposes a POST API endpoint that triggers the
computation in ```detect_object.py``` for event triggers.

## Future plans
- Add CDK code to retrieve image from S3 bucket on API trigger
- Replace all placeholder file paths
- Dockerize application for ECS deployment

## Installation
1. Clone the repository
```
git clone https://github.com/bm78g/parking-cv.git
```
2. Install the dependencies in a virtual environment
```
pip install -r requirements.txt
```
3. Run the API server
```
python src/server.py
```