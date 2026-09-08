#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.camera_upload_stack import CameraUploadStack
from infra.processing_stack import ProcessingStack


app = cdk.App()
camera_upload = CameraUploadStack(app, "CameraUploadStack")
ProcessingStack(
    app,
    "ProcessingStack",
    image_bucket=camera_upload.bucket,
)

app.synth()

