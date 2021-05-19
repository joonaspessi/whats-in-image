import botocore


def s3_object_exists(bucket, key):
    import boto3

    s3 = boto3.resource("s3")
    try:
        s3.Object(bucket, key).load()
    except botocore.exceptions.ClientError:
        return False
    return True


def test_draw_bounding_boxes(bucket, draw_bb_event, lambda_context):
    from lambdas.draw_bounding_boxes import handler

    response = handler.handler(draw_bb_event, lambda_context)
    assert s3_object_exists("testing", "labeled/01F5TK7AZHGYHMHBD1C299496F.png") is True

    assert response == [
        {
            "bucket_name": "testing",
            "object_key": "labeled/01F5TK7AZHGYHMHBD1C299496F.png",
        }
    ]
