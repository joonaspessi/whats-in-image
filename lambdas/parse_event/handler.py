import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    s3_events = _get_s3_events_from_sqs_events(event)
    return s3_events


@tracer.capture_method
def _get_s3_events_from_sqs_events(event):
    records = event["Records"]
    s3_events = []
    for record in records:
        try:
            body = json.loads(record["body"])
            s3_records = body["Records"]
        except Exception as exception:
            logger.exception("received invalid record", extra={"record": record})
            raise exception

        for s3_record in s3_records:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            object_key = s3_record["s3"]["object"]["key"]
            s3_events.append({"bucket_name": bucket_name, "object_key": object_key})
    return s3_events
