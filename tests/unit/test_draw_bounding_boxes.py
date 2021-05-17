def test_draw_bounding_boxes(bucket, draw_bb_event, lambda_context):
    from lambdas.draw_bounding_boxes import handler

    response = handler.handler(draw_bb_event, lambda_context)

    assert response == [
        {
            "bucket_name": "whatsinimagestack-whatsinimagesbucketf5245105-nmx1ow78uj0r",
            "object_key": "images/bike.png",
        }
    ]
