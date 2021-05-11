from aws_cdk import (
    aws_dynamodb,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python,
    aws_s3,
    aws_s3_notifications,
    aws_sns,
    aws_sns_subscriptions,
    aws_sqs,
    aws_stepfunctions,
    aws_stepfunctions_tasks
)
from aws_cdk import core
from aws_cdk import core as cdk


class WhatsInImageStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = aws_dynamodb.Table(
            self,
            "WhatsInImagesTable",
            partition_key=aws_dynamodb.Attribute(
                name="PK", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="SK", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=aws_dynamodb.Attribute(
                name="GSIPK1", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="GSISK1", type=aws_dynamodb.AttributeType.STRING
            ),
        )

        image_bucket = aws_s3.Bucket(
            self,
            "WhatsInImagesBucket",
            encryption=aws_s3.BucketEncryption.KMS,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
        )

        topic = aws_sns.Topic(
            self, "WhatsInImageTopic", display_name="Whats in Images Topic"
        )

        image_bucket.add_event_notification(
            aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.SnsDestination(topic),
            aws_s3.NotificationKeyFilter(prefix="images/"),
        )

        image_created_queue = aws_sqs.Queue(
            self,
            "ImageCreatedQueue",
            visibility_timeout=cdk.Duration.seconds(300),
            queue_name="ImageCreatedQueue",
            retention_period=core.Duration.hours(1),
        )

        topic.add_subscription(
            aws_sns_subscriptions.SqsSubscription(
                image_created_queue,
                raw_message_delivery=True,
            )
        )

        image_processing_lambda = aws_lambda_python.PythonFunction(
            self,
            "ImageProcessingLambda",
            entry="image_processor_lambda",
            index="image_processor_lambda.py",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "whatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
                "TABLE": table.table_name,
            },
        )

        image_bucket.grant_read(image_processing_lambda)

        image_created_queue.grant_consume_messages(image_processing_lambda)
        image_processing_lambda.add_event_source(
            aws_lambda_event_sources.SqsEventSource(
                image_created_queue,
            )
        )
        table.grant_read_write_data(image_processing_lambda)
        image_processing_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(actions=["rekognition:*"], resources=["*"])
        )

        parse_event_lambda = aws_lambda_python.PythonFunction(
            self,
            "ParseEventLambdaHandler",
            entry="lambdas/parse_event",
            index="handler.py",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "whatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
            },
        )
