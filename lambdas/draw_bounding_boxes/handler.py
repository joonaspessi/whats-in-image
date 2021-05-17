import io

import boto3
from aws_lambda_powertools import Logger, Tracer
from PIL import ExifTags, Image, ImageColor, ImageDraw, ImageFont

logger = Logger()
tracer = Tracer()


def _s3_client():
    return boto3.resource("s3")


s3 = _s3_client()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, _):
    labels = event["DetectedLabels"]["Payload"]
    keys = event["ImageKeysResult"]["Payload"]

    for key, labels in zip(keys, labels):
        s3_object = s3.Object(key["bucket_name"], key["object_key"])
        s3_response = s3_object.get()
        stream = io.BytesIO(s3_response["Body"].read())
        image = Image.open(stream)
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

        image.show()
