import boto3
import json
import time
import sys
import os

input_image = sys.argv[1]
file_name, file_extension = os.path.splitext(input_image)

s3 = boto3.client('s3')

# Create SQS client
sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/556612833346/success-destination-queue'

BUCKET_NAME = 'haiku-cam-images'

import uuid 
upload_name = uuid.uuid4().hex[:10]

s3.upload_file(input_image, BUCKET_NAME, '{}{}'.format(upload_name, file_extension))

while (1):
    print('Polling queue')
    try:
        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=5
        )
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        print((json.loads(message["Body"])["responsePayload"])['body'])

        # Delete received message from queue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        break
    except:
        print('Queue empty')
        pass
    time.sleep(2)