from dataclasses import dataclass
import os

import boto3
import pytest
from moto import mock_dynamodb


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
        aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"

    return LambdaContext()


@pytest.fixture(autouse=True, scope="session")
def aws_credentials():
  os.environ["AWS_ACCESS_KEY_ID"] = "testing"
  os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
  os.environ["AWS_SECURITY_TOKEN"] = "testing"
  os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def aws_dynamodb():
  with mock_dynamodb():
    yield boto3.client("dynamodb", region_name="us-east-1")
