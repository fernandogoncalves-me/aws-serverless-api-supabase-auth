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


@app.post("/payments/v1/confirmation")
def confirmation():
    try:
        checkout_session_id = app.current_event.get_query_string_value(name="checkout_session_id")
        confirmation = retrieve_payment_confirmation(checkout_session_id)
        email = confirmation["customer_details"]["email"]

        if confirmation["payment_status"] == "paid":
            logger.info(f"Payment confirmed for {confirmation['customer_details']['email']}")
            subscription_type = confirmation["metadata"]["subscriptionType"]
            session_credits = int(confirmation["metadata"]["sessionCredits"])
            aws.update_ddb_item(
                table_name=MEMBERS_TABLE,
                params={
                    "Key": { "Email": email},
                    "UpdateExpression": "SET SubscriptionType = :subscription_type, EarnedSessionCredits = EarnedSessionCredits + :earned_session_credits, CheckoutSessionId = :checkout_session_id",
                    "ExpressionAttributeValues": {":checkout_session_id": checkout_session_id, ":subscription_type": subscription_type, ":earned_session_credits": int(session_credits)},
                    "ConditionExpression": "SubscriptionType <> :subscription_type"
                }
            )
            
            logger.info(f"Added {subscription_type} subscription for {email}")

        return { "status": confirmation["payment_status"], "subscription_type": subscription_type, "email": email }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    stripe.api_key = aws.get_ssm_parameter(STRIPE_API_KEY_PARAM)
    return app.resolve(event, context)
