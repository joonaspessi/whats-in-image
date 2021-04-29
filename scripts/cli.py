import pprint

import boto3

TABLE = "WhatsInImageStack-WhatsInImagesTable2A25ABA1-1RSNFBDTYHI6Z"
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(TABLE)


def query_dynamodb():
    items = table.query(
        KeyConditionExpression="#PK = :pk and #SK = :sk",
        ExpressionAttributeNames={
            "#PK": "PK",
            "#SK": "SK",
        },
        ExpressionAttributeValues={
            ":pk": "IMAGE#01F4F8CZAJ3HSE361X05QHTHVQ",
            ":sk": "LABELS#01F4F8CZAJ3HSE361X05QHTHVQ",
        },
    )
    pprint.pprint(items["Items"])


query_dynamodb()
