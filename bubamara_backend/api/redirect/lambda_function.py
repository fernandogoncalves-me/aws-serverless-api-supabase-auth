import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger

from bubamara_backend.libs.aws import AWS


ALREADY_MEMBER_LINK_PARAM = os.environ["ALREADY_MEMBER_LINK_PARAM"]
MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
TRIAL_PAYMENT_LINK_PARAM = os.environ["TRIAL_PAYMENT_LINK_PARAM"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


@app.get("/redirect/v1/trial")
def trial():
    email = app.current_event.get_query_string_value(name="email")
    
    logger.info(f"Checking if member with email {email} has an active subscription...")
    member = aws.get_ddb_item(
        table_name=MEMBERS_TABLE,
        key={"Email": email}
    )
    logger.info(f"Result: {member}")

    if member:
        subscription_type = member["SubscriptionType"]
        if subscription_type != "free":
            logger.info(f"Member has an active subscription: {subscription_type}")
            redirect_url = f"{aws.get_ssm_parameter(ALREADY_MEMBER_LINK_PARAM)}?email={email}"
        else:
            logger.info("Member has a free subscription")
            redirect_url = f"{aws.get_ssm_parameter(TRIAL_PAYMENT_LINK_PARAM)}?prefilled_email={email}"
    else:
        aws.put_ddb_item(
            table_name=MEMBERS_TABLE,
            params={
                "Item": {
                    "Email": email,
                    "SubscriptionType": "free",
                    "EarnedSessionCredits": 0,
                    "UsedSessionCredits": 0,
                },
                "ConditionExpression": "attribute_not_exists(Email)"
            }
        )
        logger.info(f"Added {email} with free subscription")
        redirect_url = f"{aws.get_ssm_parameter(TRIAL_PAYMENT_LINK_PARAM)}?prefilled_email={email}"

    logger.info(f"Redirecting to {redirect_url}")
    
    return Response(
        status_code=301,
        headers={
            "Location": redirect_url
        }
    )


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    return app.resolve(event, context)
