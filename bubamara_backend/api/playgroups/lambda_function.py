import json

from aws_lambda_powertools import Logger

logger = Logger()

def lambda_handler(event, _):
    logger.info(f"Got request: {event}")
    json.loads(event["body"])
    body = {
        "sessions": [
            {
                "date": "2024-01-16",
                "start": "10:00",
                "end": "12:00",
                "location": {
                    "name": "Wijkcentrum Alleman",
                    "address": "Den Bloeyenden Wijngaerdt 1, 1183 JM Amstelveen",
                },
                "max_capacity": 10,
                "spots_available": 3,
            }
        ]
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
