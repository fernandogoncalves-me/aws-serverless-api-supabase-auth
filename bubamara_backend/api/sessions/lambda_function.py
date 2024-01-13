import json
import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger

from bubamara_backend.libs.aws import AWS


MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
SESSIONS_TABLE = os.environ["SESSIONS_TABLE"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


@app.post("/sessions/v1/reserve")
def reserve():
    try:
        body = json.loads(app.current_event.body)
        member = aws.get_ddb_item(
            table_name=MEMBERS_TABLE,
            key={"Email": body["member_email"]}
        )
        session = aws.get_ddb_item(
            table_name=SESSIONS_TABLE,
            key={"Type": body["session_type"], "DateTime": body["session_datetime"]}
        )
        # if member["AvailableSessionCredits"] > 0 and len(session["Reservations"]) < session["Capacity"]:
        #     batch_result = aws.transact_write_items(
        #         transact_items={
        #             "ConditionCheck": {

        #             }
        #             MEMBERS_TABLE: [
        #                 {
        #                     "PutRequest": {
        #                         "Item": {
        #                             "Email": body["member_email"],
        #                             "AvailableSessionCredits": member["AvailableSessionCredits"] - 1
        #                         }
        #                     }
        #                 }
        #             ],
        #             SESSIONS_TABLE: [
        #                 {
        #                     "PutRequest": {
        #                         "Item": {
        #                             "Type": body["session_type"],
        #                             "DateTime": body["session_datetime"],
        #                             "Reservations": [body["member_email"]]
        #                         }
        #                     }
        #                 }
        #             ]
        #         }
        #     )
        #     member = aws.update_ddb_item(
        #         table_name=MEMBERS_TABLE,
        #         params={
        #             "Key": {"Email": body["member_email"]},
        #             "UpdateExpression": "ADD #credits :amount",
        #             "ExpressionAttributeNames": {"#credits": "SessionCredits"},
        #             "ExpressionAttributeValues": {":amount": -1, ":minimum": 0},
        #             "ReturnValues": "UPDATED_NEW",
        #             "ConditionExpression": "#credits > :minimum"
        #         }
        #     )
        session = aws.update_ddb_item(
            table_name=SESSIONS_TABLE,
            params={
                "Key": {"Type": body["session_type"], "DateTime": body["session_datetime"]},
                "UpdateExpression": "ADD #reservations :attendee",
                "ExpressionAttributeNames": {"#reservations": "Reservations", "#capacity": "Capacity"},
                "ExpressionAttributeValues": {":attendee": [body["member_email"]]},
                "ReturnValues": "UPDATED_NEW",
                "ConditionExpression": "#credits > :minimum"
            }
        )
        logger.info(f"Updated member: {member}")

        logger.info(f"Updated session: {session}")

        return {
            "member": member,
            "session": session
        }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to add reservation. Please contact us for assistance.")


@app.post("/sessions/v1/unreserve")
def unreserve():
    try:
        body = json.loads(app.current_event.body)
        member = aws.update_ddb_item(
            table_name=MEMBERS_TABLE,
            params={
                "Key": {"Email": body["member_email"]},
                "UpdateExpression": "ADD #credits :amount",
                "ExpressionAttributeNames": {"#credits": "SessionCredits"},
                "ExpressionAttributeValues": {":amount": 1},
                "ReturnValues": "UPDATED_NEW"
            }
        )
        logger.info(f"Updated member: {member}")

        session = aws.update_ddb_item(
            table_name=SESSIONS_TABLE,
            params={
                "Key": {"Type": body["session_type"], "DateTime": body["session_datetime"]},
                "UpdateExpression": "ADD #reservations :attendee",
                "ExpressionAttributeNames": {"#reservations": "Reservations", "#capacity": "Capacity"},
                "ExpressionAttributeValues": {":attendee": [body["member_email"]]},
                "ReturnValues": "UPDATED_NEW",
                "ConditionExpression": "#credits > :minimum"
            }
        )
        logger.info(f"Updated session: {session}")

        return {
            "member": member,
            "session": session
        }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@app.get("/sessions/v1/list")
def list():
    try:
        session_type = app.current_event.get_query_string_value(name="session_type")
        pagination_key = app.current_event.get_query_string_value(name="pagination_key", default_value=None)
        
        params={
            "Limit": 15,
            "KeyConditionExpression": "#pk = :pk",
            "ExpressionAttributeNames": {"#pk": "Type"},
            "ExpressionAttributeValues": {":pk": session_type},
        }
        if pagination_key:
            params["ExclusiveStartKey"] = {"S": pagination_key}

        sessions = aws.query_ddb_items(
            table_name=SESSIONS_TABLE,
            params=params
        )
        logger.info(f"Retrieved sessions: {sessions}")

        return {"sessions": sessions}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to retrieve sessions. Please contact us for assistance.")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    return app.resolve(event, context)
