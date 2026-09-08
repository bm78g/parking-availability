from pathlib import Path
from typing import Optional
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
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct


class ProcessingStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        image_bucket: s3.IBucket,
        telemetry_table: Optional[dynamodb.ITable] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB
        self.config_table = dynamodb.Table(
            self,
            "CameraConfigTable",
            table_name="sample",
            partition_key=dynamodb.Attribute(
                name="camera_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        self.telemetry_table = telemetry_table or dynamodb.Table(
            self,
            "CameraTelemetryTable",
            partition_key=dynamodb.Attribute(
                name="camera_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # EventBridge
        self.event_bus = events.EventBus(
            self,
            "CameraEventBus",
            event_bus_name="camera-pipeline-bus",
        )

        # Resolve path to services/cv-analysis relative to this file
        cv_analysis_dir = str(
            Path(__file__).resolve().parent.parent.parent / "services" / "cv-analysis"
        )

        # OpenCV Lambda
        self.analyzer_fn = _lambda.DockerImageFunction(
            self,
            "CvAnalyzerFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                cv_analysis_dir,
                platform=ecr_assets.Platform.LINUX_ARM64,
            ),
            architecture=_lambda.Architecture.ARM_64,
            memory_size=3008,
            timeout=Duration.seconds(45),
            environment={
                "CONFIG_TABLE_NAME": self.config_table.table_name,
                "TELEMETRY_TABLE_NAME": self.telemetry_table.table_name,
                "YOLO_CONFIG_DIR": "/tmp",
                "TORCH_HOME": "/tmp",
                "HOME": "/tmp",
            },
        )

        # Permissions to read S3 image, read camera config, write telemetry
        image_bucket.grant_read(self.analyzer_fn)
        self.config_table.grant_read_data(self.analyzer_fn)
        self.telemetry_table.grant_write_data(self.analyzer_fn)

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
        cdk.CfnOutput(self, "TelemetryTableName", value=self.telemetry_table.table_name)