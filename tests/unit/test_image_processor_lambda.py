import json
import os
from dataclasses import dataclass

import boto3
import pytest
from moto import mock_s3


@pytest.fixture()
def s3_put_event():
    with open("events/s3-put.json") as file:
        event = json.load(file)
    return event


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


@pytest.fixture(autouse=True)
def environment():
    # os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    # os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    # os.environ["AWS_SECURITY_TOKEN"] = "testing"
    # os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["POWERTOOLS_TRACE_DISABLED"] = "1"
    os.environ["POWERTOOLS_SERVICE_NAME"] = "whats-in-image-testing"
    os.environ["TABLE"] = "WhatsInImageStack-WhatsInImagesTable2A25ABA1-1RSNFBDTYHI6Z"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    with mock_s3():
        yield boto3.client("s3")


def test_image_processor_lambda(s3_put_event, lambda_context):
    from image_processor_lambda import image_processor_lambda

    response = image_processor_lambda.handler(s3_put_event, lambda_context)
    assert len(response) == 1
    assert (
        response[0]["bucket_name"]
        == "whatsinimagestack-whatsinimagesbucketf5245105-nmx1ow78uj0r"
    )
    assert response[0]["object_key"] == "images/bike.png"
