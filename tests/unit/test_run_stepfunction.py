def test_run_stepfunction(s3_put_event, lambda_context, stepfunctions):
    from lambdas.run_stepfunction import handler

    response = handler.handler(s3_put_event, lambda_context)
    assert response is True
