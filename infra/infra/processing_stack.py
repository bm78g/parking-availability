import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
)
from constructs import Construct


class ProcessingStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        image_bucket: s3.IBucket,
        telemetry_table: dynamodb.ITable,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB
        self.config_table = dynamodb.Table(
            self,
            "CameraConfigTable",
            partition_key=dynamodb.Attribute(
                name="camera_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # EventBridge
        self.event_bus = events.EventBus(
            self,
            "CameraEventBus",
            event_bus_name="camera-pipeline-bus",
        )

        # OpenCV Lambda
        self.analyzer_fn = _lambda.DockerImageFunction(
            self,
            "CvAnalyzerFunction",
            code=_lambda.DockerImageCode.from_image_asset("../services/cv-analysis"),
            memory_size=3008,
            timeout=Duration.seconds(45),
            environment={
                "CONFIG_TABLE_NAME": self.config_table.table_name,
                "TELEMETRY_TABLE_NAME": telemetry_table.table_name,
            },
        )

        # Permissions to read S3 image, read camera config, write telemetry
        image_bucket.grant_read(self.analyzer_fn)
        self.config_table.grant_read_data(self.analyzer_fn)
        telemetry_table.grant_write_data(self.analyzer_fn)

        # EventBridge routing
        image_uploaded_rule = events.Rule(
            self,
            "ImageUploadedRule",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(
                source=["camera.controller"],
                detail_type=["ImageUploadCompleted"],
            ),
        )

        # Forward matching events to the CV Lambda
        image_uploaded_rule.add_target(targets.LambdaFunction(self.analyzer_fn))

        cdk.CfnOutput(self, "EventBusArn", value=self.event_bus.event_bus_arn)
        cdk.CfnOutput(self, "EventBusName", value=self.event_bus.event_bus_name)
        cdk.CfnOutput(self, "ConfigTableName", value=self.config_table.table_name)