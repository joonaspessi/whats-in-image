import io
from os import path

import boto3
from aws_lambda_powertools import Logger, Tracer
from PIL import Image, ImageDraw

logger = Logger()
tracer = Tracer()


def _s3_resource():
    return boto3.resource("s3")


def _s3_client():
    return boto3.client("s3")


s3_resource = _s3_resource()
s3_client = _s3_client()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, _):
    labels = event["DetectedLabels"]["Payload"]
    keys = event["ImageKeysResult"]["Payload"]

    bb_keys = []

    for key, labels in zip(keys, labels):
        s3_object = s3_resource.Object(key["bucket_name"], key["object_key"])
        s3_response = s3_object.get()
        stream = io.BytesIO(s3_response["Body"].read())
        image = Image.open(stream)

        image_with_labels = _draw_labels(image, labels)

        bucket = key["bucket_name"]
        image_id = path.basename(key["object_key"])
        object_key = path.join("labeled", image_id)
        _save_image_to_s3(image_with_labels, bucket=bucket, key=object_key)
        bb_keys.append({"bucket_name": bucket, "object_key": object_key})
    return bb_keys


def _draw_labels(input_image: Image, labels) -> Image:
    image = input_image.copy()
    image.format = input_image.format
    imgWidth, imgHeight = image.size
    draw = ImageDraw.Draw(image)

    for label in labels["Labels"]:
        for instance in label["Instances"]:
            box = instance["BoundingBox"]
            left = imgWidth * box["Left"]
            top = imgHeight * box["Top"]
            width = imgWidth * box["Width"]
            height = imgHeight * box["Height"]

            points = (
                (left, top),
                (left + width, top),
                (left + width, top + height),
                (left, top + height),
                (left, top),
            )

            draw.line(points, fill="#00d400", width=2)
            draw.text((left, top), f'{label["Name"]} : {label["Confidence"]}')
    return image


def _save_image_to_s3(image: Image, bucket, key):
    in_mem_file = io.BytesIO()
    image.save(in_mem_file, format=image.format)
    in_mem_file.seek(0)
    s3_client.upload_fileobj(in_mem_file, Bucket=bucket, Key=key)
