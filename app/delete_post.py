import boto3
import json
import datetime
from collections.abc import Mapping
from boto3.dynamodb.conditions import Key


bucket = 'ece1779bucket'
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def deletePost(key):
    try:
        table = dynamodb.Table('Posts')
        response = table.query(
            KeyConditionExpression=Key('Key').eq(key)
        )         
        items = response['Items']

        # get image file from s3
        if items:
            post = items[0]
            path = post['Image']
            s3_client.delete_object(Bucket=bucket, Key=path)
            table.delete_item(Key={'Key': key})
            return True
        return False
    except Exception as e:
        return False

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

        if "key" in event:
            result = deletePost(event["key"])
            if result:
                sc = 200
                result = {
                    "success": True,
                    "message": f"post with {event['key']} has been delete",
                }
            else:
                result = {
                    "success": False,
                    "message": f"Fail to delete post with {event['key']}",
                }
        response = {
            'statusCode': sc,
            'headers': {"Content-type": "application/json"},
            'body': json.dumps(result)
        }
        return response
    except Exception as e:
        return "Error:" + e