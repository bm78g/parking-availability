# I forgot I set up the REST API for EventBridge to
# trigger the CV computation via an API call, so reinstating this

# I initially thought about running this entire application through AWS lambda,
# but eventually thought against it in favor of a long-running server

# The general architecture:
# Camera system -> triggers event + adds image to S3
#   -> EventBridge calls /api/compute -> this program retrieves image from S3
#       -> Computes image -> Uploads result to DynamoDB -> API Backend serves

# This server could've provided the JSON data itself, but decided
# against it in favor of decoupling systems

from flask import Flask, jsonify
from detect_object import compute

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/health", methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Application is running"
    }), 200

@app.route("/api/compute", methods=['POST'])
def trigger_compute():
    compute()
    return jsonify({
        "status": "healthy",
        "message": "Compute successfully triggered"
    }), 200

if __name__ == "__main__":
    app.run()