def test_parse_event_lambda(s3_put_event, lambda_context):
    from lambdas.parse_event import handler

    response = handler.handler(s3_put_event, lambda_context)

    assert response == [
        {
            "bucket_name": "whatsinimagestack-whatsinimagesbucketf5245105-nmx1ow78uj0r",
            "object_key": "images/bike.png",
        }
    ]
