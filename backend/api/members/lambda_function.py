import json
import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
import requests

import stripe

from backend.libs.aws import AWS

MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
LEADS_TABLE = os.environ["LEADS_TABLE"]
STRIPE_API_KEY_PARAM = os.environ["STRIPE_API_KEY_PARAM"]
SUPABASE_API_KEY_PARAM = os.environ['SUPABASE_API_KEY_PARAM']
SUPABASE_PROJECT_PARAM = os.environ['SUPABASE_PROJECT_PARAM']
TRIAL_PAYMENT_LINK_PARAM = os.environ["TRIAL_PAYMENT_LINK_PARAM"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


def check_member_exists(email: str) -> bool:
    logger.info(f"Checking if member with email {email} exists...")
    member = aws.query_ddb_items(
        table_name=MEMBERS_TABLE,
        params={
            "IndexName": "EmailIndex",
            "KeyConditionExpression": "Email = :pk",
            "ExpressionAttributeValues": {":pk": email},
            "Limit": 1,
        }
    )
    logger.info(f"Result: {member}")

    return len(member) > 0


def retrieve_payment_confirmation(checkout_session: str) -> dict:
    logger.info(f"Retrieving payment confirmation for session {checkout_session}")
    stripe.api_key = aws.get_ssm_parameter(STRIPE_API_KEY_PARAM)
    confirmation = stripe.checkout.Session.retrieve(checkout_session)
    logger.info(f"Payment confirmation: {confirmation}")
    return confirmation


@app.get("/members/v1/member")
def member():
    try:
        member = aws.get_ddb_item(
            table_name=MEMBERS_TABLE,
            key={"MemberID": app.current_event.get_query_string_value(name="member_id")}
        )
        logger.info(f"Retrieved member: {member}")

        return {"member": member}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to retrieve member details. Please contact us for assistance.")


@app.post("/members/v1/register")
def register():
    try:
        token = app.current_event.get_header_value(name="Authorization")
        supabase_project = aws.get_ssm_parameter(SUPABASE_PROJECT_PARAM)
        supabase_api_key = aws.get_ssm_parameter(SUPABASE_API_KEY_PARAM)
        user = requests.get(
            f'https://{supabase_project}.supabase.co/auth/v1/user', 
            headers={
                'Authorization': token, 
                'apikey': supabase_api_key
            }
        ).json()
        aws.put_ddb_item(
            table_name=MEMBERS_TABLE,
            params={
                "Item": {
                    "MemberID": user["id"],
                    "Email": user["email"],
                    "SubscriptionType": "trial",
                    "EarnedSessionCredits": 1,
                    "UsedSessionCredits": 0,
                },
                "ConditionExpression": "attribute_not_exists(Email)"
            }
        )
        
        return { "status": "success" }

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@app.post("/members/v1/payment")
def payment():
    try:
        body = json.loads(app.current_event.body)

        confirmation = retrieve_payment_confirmation(body["checkout_session_id"])
        email = confirmation["customer_details"]["email"]
        payment_type = confirmation["metadata"]["paymentType"]
        response = { "status": confirmation["payment_status"], "payment_type": payment_type, "email": email }

        if confirmation["payment_status"] != "paid":
            logger.info(f"Payment not confirmed for {email}: {confirmation['payment_status']}")                
            return response

        logger.info(f"Payment confirmed for {confirmation['customer_details']['email']}")
        
        if payment_type == "trial":
            lead = aws.update_ddb_item(
                table_name=LEADS_TABLE,
                params={
                    "Key": {"Email": email},
                    "UpdateExpression": "SET PaymentStatus = :payment_status, CheckoutSessionId = :checkout_session_id",
                    "ExpressionAttributeValues": {":payment_status": "paid", ":checkout_session_id": body["checkout_session_id"]},
                    "ReturnValues": "ALL_NEW"
                }
            )
            logger.info(f"Updated lead: {lead} payment status to paid")
            response = {
                **response,
                **{
                    "status": confirmation["payment_status"],
                    "payment_type": payment_type,
                    "email": email,
                    "session": lead["Attributes"]["Session"]
                }
            }
        
        return response

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@app.post("/members/v1/trial")
def trial():
    body = json.loads(app.current_event.body)
    email = body["email"]
    member_exists = check_member_exists(email)

    if member_exists:
        logger.info(f"There is already a member with email {email}")
        response = {
            "status": "member_exists",
            "email": email
        }
    else:
        session = body["session"]
        logger.info(f"Creating a lead with {email} for session {session['SessionType']} on {session['SessionDatetime']}")
        aws.put_ddb_item(
            table_name=LEADS_TABLE,
            params={
                "Item": {
                    "Email": email,
                    "LeadSource": "trial_session",
                    "Session": session,
                    "PaymentStatus": "pending"
                }
            }
        )
        response = {
            "status": "success",
            "email": email,
            "payment_url": f"{aws.get_ssm_parameter(TRIAL_PAYMENT_LINK_PARAM)}?prefilled_email={email}"
        }

    return response
        

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    return app.resolve(event, context)
