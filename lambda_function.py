import json
import urllib.parse
import boto3
import requests
import os

s3 = boto3.client('s3')


def lambda_handler(event, context):

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    img_url = f'https://{bucket}.s3.amazonaws.com/{key}'
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(os.environ['OPENAI_SECRET_KEY']),
    }
    
    data = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Write a Haiku poem about this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_url,
                        },
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }
    
    response = requests.post(url, headers=headers, json=data)
    json_res = json.loads(response.text)
    haiku = json_res['choices'][0]['message']['content']

    output = {
        "img_url": img_url,
        "haiku": haiku
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(output)
    }
