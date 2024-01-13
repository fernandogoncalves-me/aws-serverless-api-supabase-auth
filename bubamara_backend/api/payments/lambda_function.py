import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
import stripe

from bubamara_backend.libs.aws import AWS


MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
STRIPE_API_KEY_PARAM = os.environ["STRIPE_API_KEY_PARAM"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


def retrieve_payment_confirmation(checkout_session: str) -> dict:
    logger.info(f"Retrieving payment confirmation for session {checkout_session}")
    confirmation = stripe.checkout.Session.retrieve(checkout_session)
    logger.info(f"Payment confirmation: {confirmation}")
    return confirmation


@app.post("/payments/v1/trial")
def trial():
    try:
        confirmation = retrieve_payment_confirmation(app.current_event.get_query_string_value(name="checkout_session_id"))

        if confirmation["payment_status"] == "paid":
            logger.info(f"Payment confirmed for {confirmation['customer_details']['email']}")
            aws.put_ddb_item(
                table_name=MEMBERS_TABLE,
                params={
                    "Item": {
                        "Email": confirmation["customer_details"]["email"],
                        "SubscriptionType": confirmation["metadata"]["subscriptionType"],
                        "EarnedSessionCredits": int(confirmation["metadata"]["sessionCredits"]),
                    },
                    "ConditionExpression": "attribute_not_exists(Email)"
                }
            )
            logger.info(f"Added trial subscription for {confirmation['customer_details']['email']}")

        return {"status": confirmation["payment_status"]}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@app.post("/payments/v1/membership")
def membership():
    try:
        confirmation = retrieve_payment_confirmation(app.current_event.get_query_string_value(name="checkout_session_id"))

        if confirmation["payment_status"] == "paid":
            logger.info(f"Payment confirmed for {confirmation['customer_details']['email']}")
            aws.update_ddb_item(
                table_name=MEMBERS_TABLE,
                params={
                    "Key": { "Email": confirmation["customer_details"]["email"]},
                    "AttributeUpdates": {
                        "SubscriptionType": {"Value": confirmation["metadata"]["subscriptionType"], "Action": "PUT"},
                        "EarnedSessionCredits": {"Value": int(confirmation["metadata"]["sessionCredits"]), "Action": "ADD"},
                    }
                }
            )
            logger.info(f"Added membership subscription for {confirmation['customer_details']['email']}")

        return {"status": confirmation["payment_status"]}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    stripe.api_key = aws.get_ssm_parameter(STRIPE_API_KEY_PARAM)
    return app.resolve(event, context)
