import os
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('TABLE_NAME')

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def check_user_exists(user_id):
    logger.info(f"check_user_exists {table_name}: {user_id}...")
    table = dynamodb.Table(table_name)
    logger.info(f"check_user_exists /table {table}")
    response = table.get_item(
        Key={'user_id': user_id}
    )
    logger.info(f"check_user_exists /response {response}")
    return 'Item' in response

def init_user_data(user_id, user_name, session_id):
    table = dynamodb.Table(table_name)
    item = {
            'user_id': user_id,
            'name': user_name,
            'curr_status': 'init',
            'quiz': {
                'session_id': session_id,
                'messages': [],
                'cos': ''
            }
        }
    response = table.put_item(Item=item)
    logger.info(f"init_user_data: {response}...")
    return response

def update_user_id(user_id):
    table = dynamodb.Table(table_name)
    
    response = table.get_item(Key={'user_id': user_id})
    if 'Item' not in response:
        logger.error(f"No item found for user_id: {user_id}")
        return None
    
    old_item = response['Item']
    
    new_user_id = f"{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    old_item['user_id'] = new_user_id
    put_response = table.put_item(Item=old_item)
    
    delete_response = table.delete_item(Key={'user_id': user_id})
    
    logger.info(f"user_id changed from {user_id} to {new_user_id}")
    return put_response


def insert_quiz_message(user_id, messages):
    table = dynamodb.Table(table_name)
    response = table.update_item(
        Key={
            'user_id': user_id
        },
        UpdateExpression='SET quiz.messages = list_append(quiz.messages, :m)',
        ExpressionAttributeValues={
            ':m': messages
        },
        ConditionExpression=Attr('quiz.messages').exists(),
        ReturnValues='UPDATED_NEW'
    )
    return response

def get_user_name(user_id):
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={'user_id': user_id}
    )
    if 'Item' in response:
        return response['Item']['name']
    return None

def set_user_curr_status(user_id, curr_status):
    table = dynamodb.Table(table_name)
    response = table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET curr_status = :s',
        ExpressionAttributeValues={
            ':s': curr_status
        },
        ReturnValues='UPDATED_NEW'
    )
    return response

def get_user_curr_status(user_id):
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={'user_id': user_id}
    )
    if 'Item' in response:
        return response['Item']['curr_status']
    return None

def get_user_quiz_messages(user_id):
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={'user_id': user_id}
    )
    if 'Item' in response:
        return response['Item']['quiz']['messages']
    return None

def get_seesion_id(user_id):
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={'user_id': user_id}
    )
    if 'Item' in response:
        return response['Item']['quiz']['session_id']
    return None

def set_quiz_cos(user_id, cos_value):
    table = dynamodb.Table(table_name)
    response = table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET quiz.cos = :c',
        ExpressionAttributeValues={
            ':c': cos_value
        },
        ConditionExpression=Attr('quiz').exists(),
        ReturnValues='UPDATED_NEW'
    )
    return response

def get_quiz_cos(user_id):
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={'user_id': user_id}
    )
    if 'Item' in response and 'quiz' in response['Item'] and 'cos' in response['Item']['quiz']:
        return response['Item']['quiz']['cos']
    return None