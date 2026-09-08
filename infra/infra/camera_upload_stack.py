from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigw
)
from constructs import Construct

class CameraUploadStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self, "CameraRawUploads",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        self.presign_fn = _lambda.Function(
            self, "PresignURLFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.main",
            code=_lambda.Code.from_asset("lambda_presign"),
            timeout=Duration.seconds(5),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name
            }
        )

        self.bucket.grant_put(self.presign_fn)

        api = apigw.RestApi(self, "CameraApi", deploy_options=apigw.StageOptions(stage_name="v1"))
        upload_endpoint = api.root.add_resource("get-upload-url")
        upload_endpoint.add_method("POST", apigw.LambdaIntegration(self.presign_fn))