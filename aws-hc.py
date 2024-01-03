import boto3
import json
import time
import os
import subprocess
from dotenv import load_dotenv

from picamera import PiCamera
from time import sleep
from gpiozero import Button

from urllib.request import urlopen
from urllib.error import URLError

load_dotenv()

# wait for internet connection
while True:
    try:
        urlopen('https://www.google.com/',timeout=1)
        break
    except URLError:
        pass

o = subprocess.check_output('hostname -I', shell=True)
print(o)
subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/demo \"ip\" \"{}\" \"\"".format(o)], shell=True)

camera = PiCamera()
button = Button(17)

while True:
    print('wait for push...')
    button.wait_for_press()
    print('pushed')
    sleep(2)
    camera.capture('/home/saarthak/Desktop/test.jpg')
    print('image saved')
    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/demo \"load\" \"\" \"\""], shell=True)

    input_image = '/home/saarthak/Desktop/test.jpg'
    file_name, file_extension = os.path.splitext(input_image)

    session = boto3.Session(
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name = 'us-east-1'
    )

    s3 = session.client('s3')
    sqs = session.client('sqs')
    queue_url = os.getenv("QUEUE_URL")
    BUCKET_NAME = os.getenv("BUCKET_NAME")

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
            response = json.loads((json.loads(message["Body"])["responsePayload"])['body'])
            print((json.loads(message["Body"])["responsePayload"])['body'])
            print(type(response))

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

    lines = response['haiku'].splitlines()
    print(lines)

    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/demo \"{}\" \"{}\" \"{}\"".format(lines[0], lines[1], lines[2])], shell=True)
