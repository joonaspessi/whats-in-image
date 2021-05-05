import os
import pprint

import boto3
import botocore
import click

dynamodb = boto3.resource("dynamodb")


@click.group()
def cli():
    pass


@click.command(help="Print contents of DynamoDB table")
@click.option("--table", required=True, help="DynamoDB table name")
def scan(table):
    ddb_table = dynamodb.Table(table)
    try:
        items = ddb_table.scan()
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Given table={table} not found.")
            quit(os.EX_DATAERR)
        raise error

    pprint.pprint(items["Items"])


@click.command(help="Get specific item from DynamoDB")
@click.option("--table", required=True, help="DynamoDB table name")
@click.option("--id", required=True, help="Item id")
def query(table, id):
    ddb_table = dynamodb.Table(table)
    try:
        items = ddb_table.query(
            KeyConditionExpression="#PK = :pk and #SK = :sk",
            ExpressionAttributeNames={
                "#PK": "PK",
                "#SK": "SK",
            },
            ExpressionAttributeValues={
                ":pk": f"IMAGE#{id}",
                ":sk": f"IMAGE#{id}",
            },
        )
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Given table={table} not found.")
            quit(os.EX_DATAERR)
        raise error
    if not len(items["Items"]):
        print(f"id={id} not found in Dynamodb table={table}")
        quit(os.EX_DATAERR)
    pprint.pprint(items["Items"])


cli.add_command(scan)
cli.add_command(query)

if __name__ == "__main__":
    cli()
