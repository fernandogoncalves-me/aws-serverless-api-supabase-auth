import json
import os

import pytest

from backend.api.members.lambda_function import lambda_handler

MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]


class TestMembers:
    def _get_http_event(self, path: str, method: str = "POST", body: str = None, query_string_params: dict = None) -> dict:
        event = {
          "httpMethod": method,
          "rawPath": f"/test{path}",
          "requestContext": {
            "http": {
              "method": method,
              "path": f"/test{path}"
            },
            "requestId": "227b78aa-779d-47d4-a48e-ce62120393b8",
            "stage": "test",
          }
        }

        if body:
            event["body"] = body

        if query_string_params:
            event["queryStringParameters"] = query_string_params

        return event
        
    @pytest.mark.parametrize(
            "member_data",
            [
                {
                  "MemberID": {"S": "test_id"},
                  "Email": {"S": "foo@bar.com"},
                  "SubscriptionType": {"S": "trial"},
                  "EarnedSessionCredits": {"N": "1"},
                  "UsedSessionCredits": {"N": "0"},
              }
            ]
    )
    def test_can_get_member(self, member_data, members_table, lambda_context):
        members_table.put_item(
            TableName=MEMBERS_TABLE,
            Item=member_data,
        )

        member = lambda_handler(self._get_http_event(
            "/members/v1/member",
            "GET",
            query_string_params={"member_id": "test_id"}

        ), lambda_context)

        assert member["statusCode"] == 200
        assert json.loads(member["body"])["member"]["MemberID"] == member_data["MemberID"]["S"]
