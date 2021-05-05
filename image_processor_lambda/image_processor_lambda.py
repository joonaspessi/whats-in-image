import datetime
import json
import os

import boto3
import ulid
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
metrics = Metrics()
tracer = Tracer()

dynamodb = boto3.resource("dynamodb")
rekognition = boto3.client("rekognition")
table = dynamodb.Table(os.environ["TABLE"])


@metrics.log_metrics
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    processed_at = datetime.datetime.utcnow().isoformat()
    images = _get_images_from_sqs_event(event)

    results = []
    for image in images:
        params = {
            "S3Object": {"Bucket": image["bucket_name"], "Name": image["object_key"]}
        }
        try:
            result = rekognition.detect_labels(
                Image=params, MaxLabels=10, MinConfidence=60
            )
        except Exception as exception:
            logger.exception("AWS rekognition raised error")
            raise exception
        results.append(result)

    _insert_to_dynamoDB(images, results, processed_at=processed_at)
    metrics.add_metric(name="ImageLabeled", unit=MetricUnit.Count, value=1)
    return images


@tracer.capture_method
def _get_images_from_sqs_event(event):
    records = event["Records"]
    images = []
    for record in records:
        try:
            body = json.loads(record["body"])
            s3_records = body["Records"]
        except Exception as exception:
            logger.exception("received invalid record", extra={"record": record})
            raise exception

        for s3_record in s3_records:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            object_key = s3_record["s3"]["object"]["key"]
            images.append({"bucket_name": bucket_name, "object_key": object_key})
    return images


@tracer.capture_method
def _insert_to_dynamoDB(images, results, processed_at):
    for image, result in zip(images, results):
        image_id = ulid.new()
        logger.info(result)
        labels = _get_labels(result)
        table.put_item(
            Item={
                "PK": "IMAGE#" + image_id.str,
                "SK": "IMAGE#" + image_id.str,
                "labels": json.dumps(labels),
                "bucket_name": image["bucket_name"],
                "object_key": image["object_key"],
                "type": "image",
                "processed_at": processed_at,
            }
        )


@tracer.capture_method
def _get_labels(result):
    return result["Labels"]
