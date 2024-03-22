import os

import pytest

MEMBERS_TABLE=os.environ["MEMBERS_TABLE"]

@pytest.fixture(scope="function")
def members_table(aws_dynamodb):
    aws_dynamodb.create_table(
        TableName=MEMBERS_TABLE,
        KeySchema=[
            {"AttributeName": "MemberID", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "MemberID", "AttributeType": "S"},
            {"AttributeName": "Email", "AttributeType": "S"},
            {"AttributeName": "SubscriptionType", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        GlobalSecondaryIndexes=[
            {
                "IndexName": "EmailIndex",
                "KeySchema": [
                    {"AttributeName": "Email", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            },
            {
                "IndexName": "SubscriptionTypeIndex",
                "KeySchema": [
                    {"AttributeName": "SubscriptionType", "KeyType": "HASH"},
                    {"AttributeName": "MemberID", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            },
        ]
    )

    yield aws_dynamodb
