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
)
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as stepfunctions_tasks
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
            tracing=aws_lambda.Tracing.ACTIVE,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
        )

        detect_labels_lambda = aws_lambda_python.PythonFunction(
            self,
            "DetectLabelsLambdaHandler",
            entry="lambdas/detect_labels",
            index="handler.py",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "whatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
            },
            tracing=aws_lambda.Tracing.ACTIVE,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
        )

        image_bucket.grant_read(detect_labels_lambda)

        detect_labels_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(actions=["rekognition:*"], resources=["*"])
        )

        draw_bounding_boxes_lambda = aws_lambda_python.PythonFunction(
            self,
            "DrawBoundingBoxesLambdaHandler",
            entry="lambdas/draw_bounding_boxes",
            index="handler.py",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "WhatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
            },
            tracing=aws_lambda.Tracing.ACTIVE,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            timeout=core.Duration.seconds(120),
            memory_size=1024,
        )

        image_bucket.grant_read_write(draw_bounding_boxes_lambda)

        store_dynamodb_lambda = aws_lambda_python.PythonFunction(
            self,
            "StoreDynamoDBLambdaHandler",
            entry="lambdas/store_dynamodb",
            index="handler.py",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "whatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
                "TABLE": table.table_name,
            },
            tracing=aws_lambda.Tracing.ACTIVE,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
        )

        table.grant_read_write_data(store_dynamodb_lambda)

        image_label_succeeded = stepfunctions.Succeed(self, "Image succesfully labeled")
        image_label_failed = stepfunctions.Fail(self, "Could not label given input")

        parse_event_step = stepfunctions.Task(
            self,
            "ParseEvent",
            task=stepfunctions_tasks.RunLambdaTask(parse_event_lambda),
            result_path="$.ImageKeysResult",
        ).add_catch(image_label_failed)

        detect_labels_step = stepfunctions.Task(
            self,
            "DetectLabels",
            task=stepfunctions_tasks.RunLambdaTask(detect_labels_lambda),
            result_path="$.DetectedLabels",
        ).add_catch(image_label_failed)

        draw_bounding_boxes_step = stepfunctions.Task(
            self,
            "DrawBoundingBoxes",
            task=stepfunctions_tasks.RunLambdaTask(draw_bounding_boxes_lambda),
            result_path="$.BoundingBoxKeysResult",
            timeout=core.Duration.seconds(120),
        ).add_catch(image_label_failed)

        store_dynamodb_step = stepfunctions.Task(
            self,
            "StoreDynamoDB",
            task=stepfunctions_tasks.RunLambdaTask(store_dynamodb_lambda),
        ).add_catch(image_label_failed)

        defintion = (
            stepfunctions.Chain.start(parse_event_step)
            .next(detect_labels_step)
            .next(draw_bounding_boxes_step)
            .next(store_dynamodb_step)
            .next(image_label_succeeded)
        )

        image_labeling_stepfunction = stepfunctions.StateMachine(
            self,
            "ImageLabeling",
            definition=defintion,
            timeout=core.Duration.minutes(10),
            tracing_enabled=True,
        )

        trigger_image_labeling_lambda = aws_lambda_python.PythonFunction(
            self,
            "TriggerImageLabelingStepFunction",
            entry="lambdas/run_stepfunction",
            index="handler.py",
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "whatsInImage",
                "POWERTOOLS_METRICS_NAMESPACE": "whatsInImage",
                "STEPFUNCTION_ARN": image_labeling_stepfunction.state_machine_arn,
            },
            tracing=aws_lambda.Tracing.ACTIVE,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
        )

        image_created_queue.grant_consume_messages(trigger_image_labeling_lambda)
        trigger_image_labeling_lambda.add_event_source(
            aws_lambda_event_sources.SqsEventSource(
                image_created_queue,
            )
        )

        image_labeling_stepfunction.grant_start_execution(trigger_image_labeling_lambda)
