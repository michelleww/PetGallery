import boto3
import json
import datetime
from collections.abc import Mapping
from boto3.dynamodb.conditions import Key

bucket = 'ece1779bucket'
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def count_entries(table_name):
    try:
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        return len(items)
    except Exception as e:
        return 0

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

        total_posts = count_entries('Posts')
        total_users = count_entries('Users')
        sc = 200
        result = {
            "success": True,
            "total_posts": total_posts,
            "total_users": total_users
        }
        response = {
            'statusCode': sc,
            'headers': {"Content-type": "application/json"},
            'body': json.dumps(result)
        }
        return response
    except Exception as e:
        return "Error:" + e