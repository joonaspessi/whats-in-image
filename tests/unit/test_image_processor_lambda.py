import json


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
