import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


def _rekognition_client():
    return boto3.client("rekognition", region_name="eu-west-1")


rekognition = _rekognition_client()


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    images_to_label = event["ImageKeysResult"]["Payload"]

    results = []

    for image_key in images_to_label:
        params = {
            "S3Object": {
                "Bucket": image_key["bucket_name"],
                "Name": image_key["object_key"],
            }
        }
        result = _detect_labels(params)
        results.append(result)

    return results


@tracer.capture_method
def _detect_labels(bucket, max_labels=10, min_confidence=60):
    labels = rekognition.detect_labels(Image=bucket, MaxLabels=10, MinConfidence=60)
    logger.info(labels)
    return labels
