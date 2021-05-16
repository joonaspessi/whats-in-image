import json
import os
from datetime import datetime
from os import path

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()


def _dynamodb_table():
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = dynamodb.Table(os.environ["TABLE"])
    return table


table = _dynamodb_table()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, _):
    labels = event["DetectedLabels"]["Payload"]
    keys = event["ImageKeysResult"]["Payload"]
    processed_at = datetime.utcnow().isoformat()

    _insert_to_dynamoDB(keys, labels, processed_at)
    metrics.add_metric(name="ImageLabeled", unit=MetricUnit.Count, value=1)


@tracer.capture_method
def _insert_to_dynamoDB(keys, labels, processed_at):

    with table.batch_writer() as batch:
        for key, labels in zip(keys, labels):
            item_id = path.splitext(path.basename(key["object_key"]))[0]
            batch.put_item(
                Item={
                    "PK": "IMAGE#" + item_id,
                    "SK": "IMAGE#" + item_id,
                    "labels": json.dumps(labels["Labels"]),
                    "bucket_name": key["bucket_name"],
                    "object_key": key["object_key"],
                    "type": "image",
                    "processed_at": processed_at,
                }
            )
