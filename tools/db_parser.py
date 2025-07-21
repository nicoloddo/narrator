# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 16:46:34 2024

@author: nicol
"""

import boto3
import json
import asyncio
from botocore.exceptions import ClientError

from utils.env_utils import get_env_var

# Initialize the SQS client
sqs = boto3.client(
    "sqs",
    region_name=get_env_var("AWS_REGION"),
    aws_access_key_id=get_env_var("AWS_QUEUE_KEY_ID"),
    aws_secret_access_key=get_env_var("AWS_QUEUE_API_KEY"),
)

# SQS queue URL
queue_url = get_env_var("AWS_QUEUE")


def process_message(message):
    # Parse the message body
    body = json.loads(message["Body"])

    # Extract id
    entry_id = message["MessageId"]
    print(f"Processing new entry with ID: {entry_id}")

    body["id"] = entry_id

    # Process the new entry
    return body


async def fetch_record(verbose=False):
    try:
        # Receive messages from SQS FIFO queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0,  # Short polling
            AttributeNames=["MessageGroupId"],
        )

        # Process message if received
        messages = response.get("Messages", [])
        if messages:
            message = messages[0]
            if verbose:
                print(f"New message: {message}")
            try:
                record = process_message(message)

                # Delete the message from the queue after successful processing
                sqs.delete_message(
                    QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
                )
                if verbose:
                    print(
                        f"Successfully processed and deleted message: {message['MessageId']}"
                    )
                    print(
                        f"Message Group ID: {message['Attributes']['MessageGroupId']}"
                    )

                return record

            except Exception as e:
                print(f"Error processing message {message['MessageId']}: {e}")
                # Message will return to the queue after visibility timeout
        else:
            if verbose:
                # print("No messages found.")
                pass

    except ClientError as e:
        print(f"An error occurred: {e}")
        await asyncio.sleep(5)  # Wait a bit longer on errors
