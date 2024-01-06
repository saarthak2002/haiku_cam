import boto3
import json
import time
import sys
import os
import subprocess
import qrcode
from PIL import Image
import uuid

from picamera import PiCamera
from time import sleep
from gpiozero import Button

from urllib.request import urlopen
from urllib.error import URLError

from dotenv import load_dotenv
load_dotenv()

import sqlite3
con = sqlite3.connect("/home/saarthak/haiku.db")
cur = con.cursor()

def generate_qr_code(link):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=0,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save("qrcode.png")
    return img

def qr_to_array(qr_img):
    pixels = qr_img.load()
    width, height = qr_img.size
    pixel_array = [[0 for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            # Check if the pixel is black or white
            pixel_array[y][x] = 0 if pixels[x, y] == 0 else 1

    return pixel_array

# Check internet connection
while True:
    try:
        urlopen('https://www.google.com/',timeout=1)
        break
    except URLError:
        pass

o = subprocess.check_output('hostname -I', shell=True)
subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/lcd_interface \"ip\" \"{}\" \"\"".format(o)], shell=True)

camera = PiCamera()
button = Button(17)

while True:
    # Capture image on button press
    print('wait for push...')
    button.wait_for_press()
    print('pushed')
    sleep(2)
    camera.capture('/home/saarthak/Desktop/test.jpg')
    print('image saved')
    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/lcd_interface \"load\" \"\" \"\""], shell=True)

    # Upload image to S3 Bucket
    input_image = '/home/saarthak/Desktop/test.jpg'
    file_name, file_extension = os.path.splitext(input_image)

    session = boto3.Session(
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name = 'us-east-1'
    )

    s3 = session.client('s3')
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    sqs = session.client('sqs')
    queue_url = os.getenv('QUEUE_URL')

    upload_name = uuid.uuid4().hex[:10]
    s3.upload_file(input_image, BUCKET_NAME, '{}{}'.format(upload_name, file_extension))

    # Poll SQS for response
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
    image_s3_url = response['img_url']
    
    # Add record to sqlite database
    insert_data = (image_s3_url, response['haiku'])
    sqlite_insert_with_param = """INSERT INTO haiku (image, poem) VALUES (?, ?);"""
    cur.execute(sqlite_insert_with_param, insert_data)
    con.commit()

    # Print poem and QR code to LCD display
    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/lcd_interface \"{}\" \"{}\" \"{}\"".format(lines[0], lines[1], lines[2])], shell=True)

    qr_code = generate_qr_code(image_s3_url)
    qr_array = qr_to_array(qr_code)
    flat_qr_array = [item for sublist in qr_array for item in sublist]
    qr_str = ''.join([str(elem) for elem in flat_qr_array])
    
    time.sleep(10)
    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/lcd_interface \"qr\" \"{}\" \"\"".format(qr_str)], shell=True)
    time.sleep(10)
    subprocess.run(["sudo /home/saarthak/ili9225spi_rpi/lcd_interface \"ready\" \"\" \"\""], shell=True)
