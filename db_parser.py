# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 16:46:34 2024

@author: nicol
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

from env_utils import get_env_var

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


def fetch_record(debug_chat=False):
    """
    Fetch a record from the SQS queue.

    Args:
        debug_chat (bool): If True, returns a mock record for testing

    Returns:
        dict: The processed message body with added 'id' field
    """

    if debug_chat:
        print("Debug mode: returning mock record")
        return {
            "id": "debug-123",
            "mode": "ask_davide",
            "content": "This is a debug message for testing the chat functionality.",
        }

    while True:
        try:
            # Receive message from SQS queue
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                VisibilityTimeoutSeconds=30,
            )

            # Check if we received any messages
            if "Messages" in response:
                message = response["Messages"][0]

                # Process the message
                processed_body = process_message(message)

                # Delete the message from the queue
                sqs.delete_message(
                    QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
                )

                return processed_body
            else:
                print("No messages received, continuing to poll...")

        except ClientError as e:
            print(f"Error receiving message: {e}")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)  # Wait before retrying
