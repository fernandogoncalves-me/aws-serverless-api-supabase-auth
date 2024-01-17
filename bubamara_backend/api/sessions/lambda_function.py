import datetime
import json
import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger

from bubamara_backend.libs.aws import AWS


MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
RESERVATIONS_TABLE = os.environ["RESERVATIONS_TABLE"]
SESSIONS_TABLE = os.environ["SESSIONS_TABLE"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()

@app.get("/sessions/v1/reservations")
def reservations():
    try:
        email = app.current_event.get_query_string_value(name="email")
        session_type = app.current_event.get_query_string_value(name="session_type")
        pagination_key = app.current_event.get_query_string_value(name="pagination_key", default_value=None)
        
        params={
            "Limit": 15,
            "KeyConditionExpression": "Email = :pk and begins_with(ReservationType, :sk)",
            "ExpressionAttributeValues": {":pk": email, ":sk": session_type},
        }
        if pagination_key:
            params["ExclusiveStartKey"] = {"S": pagination_key}

        reservations = aws.query_ddb_items(
            table_name=RESERVATIONS_TABLE,
            params=params
        )
        logger.info(f"Retrieved reservations: {reservations}")

        return {"reservations": reservations}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to retrieve sessions. Please contact us for assistance.")

@app.post("/sessions/v1/reserve")
def reserve():
    try:
        body = json.loads(app.current_event.body)
        result = aws.transact_write_items(
            transact_items=[
                {
                    "Put": {
                        "TableName": RESERVATIONS_TABLE,
                        "Item": {"Email": {"S": body["member_email"]}, "ReservationType": {"S": f"{body['session_type']}#{body['session_datetime']}"}},
                        "ConditionExpression": "attribute_not_exists(Email) and attribute_not_exists(ReservationType)"
                    }
                },
                {
                    "Update": {
                        "TableName": SESSIONS_TABLE,
                        "Key": {"SessionType": {"S": body["session_type"]}, "SessionDatetime": {"S": body["session_datetime"]}},
                        "UpdateExpression": "ADD Reservations :increment",
                        "ExpressionAttributeValues": {":increment": {"N": "1"},},
                        "ConditionExpression": "Reservations < MaxCapacity"
                    }
                },
                {
                    "Update": {
                        "TableName": MEMBERS_TABLE,
                        "Key": {"Email": {"S": body["member_email"]}},
                        "UpdateExpression": "ADD UsedSessionCredits :increment",
                        "ExpressionAttributeValues": {":increment": {"N": "1"},},
                        "ConditionExpression": "UsedSessionCredits < EarnedSessionCredits"
                    }
                }
            ]
        )
        logger.info(f"Reservation result: {result}")

        return { "status": "reserved" }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to add reservation. Please contact us for assistance.")


@app.post("/sessions/v1/unreserve")
def unreserve():
    try:
        body = json.loads(app.current_event.body)
        logger.info("Canceling reservation")
        result = aws.transact_write_items(
            transact_items=[
                {
                    "Delete": {
                        "TableName": RESERVATIONS_TABLE,
                        "Key": {"Email": {"S": body["member_email"]}, "ReservationType": {"S": f"{body['session_type']}#{body['session_datetime']}"}},
                        "ConditionExpression": "attribute_exists(Email) and attribute_exists(ReservationType)"
                    }
                },
                {
                    "Update": {
                        "TableName": MEMBERS_TABLE,
                        "Key": {"Email": {"S": body["member_email"]}},
                        "UpdateExpression": "ADD UsedSessionCredits :decrement",
                        "ExpressionAttributeValues": {":decrement": {"N": "-1"},}
                    }
                },
                {
                    "Update": {
                        "TableName": SESSIONS_TABLE,
                        "Key": {"SessionType": {"S": body["session_type"]}, "SessionDatetime": {"S": body["session_datetime"]}},
                        "UpdateExpression": "ADD Reservations :decrement",
                        "ExpressionAttributeValues": {":decrement": {"N": "-1"},}
                    }
                }
            ]
        )
        logger.info(f"Unreserve result: {result}")

        return { "status": "unreserved" }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to cancel reservation. Please contact us for assistance.")


@app.get("/sessions/v1/list")
def list():
    try:
        session_type = app.current_event.get_query_string_value(name="session_type")
        pagination_key = app.current_event.get_query_string_value(name="pagination_key", default_value=None)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        
        params={
            "Limit": 15,
            "KeyConditionExpression": "SessionType = :pk and SessionDatetime > :sk",
            "ExpressionAttributeValues": {":pk": session_type, ":sk": tomorrow.strftime("%Y-%m-%d")},
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
