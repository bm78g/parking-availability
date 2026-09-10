# Automated Parking Occupancy Detection System

## Overview

This project is a AWS cloud-based microservice system that uses computer vision
and ML object detection to determine occupancy of a parking lot photo.

## Architecture

The system consists of the following:
- Raspberry Pi & Camera controller
- Computer vision program
- Backend server (May be replaced with an API Gateway & Lambda)
- Frontend server

### Camera & Upload

The camera takes a picture every few seconds and uploads it to an S3 bucket
using the camera ID as its key.

The S3 upload is indirect, querying an API Gateway to generate a presigned
URL using a Lambda function to avoid storing access keys in the machine.

### Image Processing

The camera also pushes an event towards EventBridge, which triggers another
Lambda function that uses OpenCV and a YOLO model to analyze the uploaded
image and identify occupancies.

The analysis works as follows:
1. The user is to run ```calibration.py``` within ```cv-analysis/src``` to
draw bounds of each parking spot and store the information as JSON data.
2. The JSON data is to be pushed to DynamoDB using ```upload_bounds.py```.
3. ```detect_object.py``` is triggered by EventBridge and retrieves the
corresponding bounds JSON data, detects where each vehicle is, then compares
the positions of the vehicles to the bounds of each parking spot. Each
vehicle makes a connection to a parking spot (if parked) and outputs a JSON
file that lists the occupancy status of each spot.
4. The JSON data is used to update the corresponding file in DynamoDB.

### Web Usage

The backend server will then expose an endoint that retrieves the occupancy
data for the requested parking lot from DynamoDB.

The frontend server will query the backend server for the information it
needs and display it to the users in a digestible format.

## Usage

The repository is to be cloned into each camera, define the API gateway URL
in ```.env```, then run ```main.py``` inside ```camera-controller/src```

## Status/Roadmap

- [x] Make camera take picture and save it as a file
- [x] Create calibration tools for drawing bounds of a parking lot
- [x] Compare calibrated bounds with detected vehicle locations
- [ ] Define CDK stacks
    - [x] Define camera upload stack
    - [x] Define image processing stack
    - [ ] Define web stack
- [x] Integrate AWS services
    - Camera Controller
        - [x] Upload camera images to S3
            - [x] Write Lambda function for generating presigned URL
            - [x] Trigger EventBridge
    - CV Analysis
        - [x] Manually upload bounds calibration data to DynamoDB
        - [x] Retrieve bounds calibration data from DynamoDB
        - [x] Retrieve image from DynamoDB
        - [x] Upload analysis result to DynamoDB
- [ ] Write backend server (may replace with API Gateway)
- [ ] Write frontend server
    - [ ] Define method of displaying JSON data