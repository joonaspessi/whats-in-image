import json
import os
from dataclasses import dataclass
from unittest.mock import patch

import boto3
import pytest
from botocore.stub import Stubber
from moto import mock_dynamodb2, mock_s3


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
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

    os.environ["POWERTOOLS_TRACE_DISABLED"] = "1"
    os.environ["POWERTOOLS_SERVICE_NAME"] = "testing"
    os.environ["POWERTOOLS_METRICS_NAMESPACE"] = "testing"

    os.environ["TABLE"] = "testing"
    os.environ["BUCKET"] = "testing"
    os.environ["REGION"] = "eu-west-1"


@pytest.fixture(scope="function")
def s3(environment):
    with mock_s3():
        yield boto3.client("s3", region_name=os.environ["REGION"])


@pytest.fixture(scope="function")
def dynamodb(environment):
    with mock_dynamodb2():
        yield boto3.resource("dynamodb", region_name=os.environ["REGION"])


@pytest.fixture(scope="function")
def table(dynamodb):
    table = dynamodb.create_table(
        TableName=os.environ["TABLE"],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
    )
    table.meta.client.get_waiter("table_exists").wait(TableName=os.environ["TABLE"])

    assert table.item_count == 0

    return table


@pytest.fixture(scope="function")
def bucket(s3):
    location = {"LocationConstraint": os.environ["REGION"]}
    s3.create_bucket(Bucket=os.environ["BUCKET"], CreateBucketConfiguration=location)
    s3.upload_file(
        "./tests/assets/test_image.png", os.environ["BUCKET"], "images/test_image.png"
    )
    return s3


@pytest.fixture(scope="function")
def label_mock():
    with patch(
        "image_processor_lambda.image_processor_lambda._detect_labels"
    ) as mock_client:
        mock_client.return_value = {"Labels": []}
        yield


def test_image_processor_lambda(
    s3_put_event, lambda_context, bucket, table, label_mock
):
    from image_processor_lambda import image_processor_lambda

    image_processor_lambda.handler(s3_put_event, lambda_context)

    response = table.scan()
    items = response["Items"]
    assert len(items) == 1
    item = items[0]

    assert (
        item["bucket_name"]
        == "whatsinimagestack-whatsinimagesbucketf5245105-nmx1ow78uj0r"
    )
    assert item["object_key"] == "images/bike.png"
    assert item["type"] == "image"
    assert json.loads(item["labels"]) == []
