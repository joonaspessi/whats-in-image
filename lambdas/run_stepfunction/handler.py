import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()

stepfunctions = boto3.client("stepfunctions")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    stepfunctions.start_execution(
        stateMachineArn=os.environ["STEPFUNCTION_ARN"], input=json.dumps(event)
    )
    return True
