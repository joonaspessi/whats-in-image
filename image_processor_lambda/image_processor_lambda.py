import json
import os

import boto3
import ulid
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()

rekognition = boto3.client("rekognition")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE"])


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    records = event["Records"]

    images = []
    for record in records:
        try:
            body = json.loads(record["body"])
            s3_records = body["Records"]
        except:
            logger.exception("received invalid record", extra={"record": record})

        for s3_record in s3_records:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            object_key = s3_record["s3"]["object"]["key"]
            images.append({"bucket_name": bucket_name, "object_key": object_key})

    results = []
    for image in images:
        params = {
            "S3Object": {"Bucket": image["bucket_name"], "Name": image["object_key"]}
        }
        result = rekognition.detect_labels(Image=params, MaxLabels=10, MinConfidence=60)
        logger.info(result)
        results.append(result)

    _insert_to_dynamoDB(images, results)
    return images


def _insert_to_dynamoDB(images, results):
    for image, result in zip(images, results):
        image_id = ulid.new()
        labels = _get_labels(result)
        table.put_item(
            Item={
                "PK": "IMAGE#" + image_id.str,
                "SK": "LABELS#" + image_id.str,
                "labels": labels,
                "bucket_name": image["bucket_name"],
                "object_key": image["object_key"],
            }
        )


def _get_labels(result):
    labels = set()
    for rekog in result["Labels"]:
        labels.add(rekog["Name"])
    return list(labels)
