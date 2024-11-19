import boto3
import json
import datetime
from collections.abc import Mapping
from boto3.dynamodb.conditions import Key
import botocore

bucket = 'ece1779bucket'
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def lambda_handler(event, context):
    try:
        if 'queryStringParameters' in event and event['queryStringParameters'] != None:
            event = event["queryStringParameters"]
        else:
            if isinstance(event["body"], Mapping):
                event = event["body"]
            else:
                event = json.loads(event["body"])

        sc = None  # Status code
        result = ""  # Response payload

        # Traverse all posts and delete the post if it's image not exist in S3
        table = dynamodb.Table('Posts')
        response = table.scan()
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        for item in items:
            path = item['Image']
            try:
                s3_resource.Object(bucket, path).load()
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    table.delete_item(Key={'Key': item['Key']})
                else:
                    continue

        response = {
            'statusCode': sc,
            'headers': {"Content-type": "application/json"},
        }
        return response

    except Exception as e:
        return "Error:" + e