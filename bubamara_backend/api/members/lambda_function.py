import json
import os
import string
import random

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
import requests

import stripe

from bubamara_backend.libs.aws import AWS

TRIAL_ACTIVE_LINK_PARAM = os.environ["TRIAL_ACTIVE_LINK_PARAM"]
TRIAL_PAYMENT_LINK_PARAM = os.environ["TRIAL_PAYMENT_LINK_PARAM"]

MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]
LEADS_TABLE = os.environ["LEADS_TABLE"]

STRIPE_API_KEY_PARAM = os.environ["STRIPE_API_KEY_PARAM"]
SUPABASE_API_KEY_PARAM = os.environ['SUPABASE_API_KEY_PARAM']
SUPABASE_PROJECT_PARAM = os.environ['SUPABASE_PROJECT_PARAM']
SUPABASE_SECRET_KEY_PARAM = os.environ['SUPABASE_SECRET_KEY_PARAM']

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


def add_member_with_temp_password(email: str):
    try:
        user_uid, temp_password = create_supabase_user(email)
        aws.put_ddb_item(
            table_name=MEMBERS_TABLE,
            params={
                "Item": {
                    "MemberID": user_uid,
                    "Email": email,
                    "SubscriptionType": "trial",
                    "EarnedSessionCredits": 1,
                    "UsedSessionCredits": 0,
                },
                "ConditionExpression": "attribute_not_exists(Email)"
            }
        )
    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to sign up member. Please contact us for assistance.")

    return temp_password


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


def create_supabase_user(email: str):
    supabase_api_key = aws.get_ssm_parameter(SUPABASE_API_KEY_PARAM)
    supabase_project = aws.get_ssm_parameter(SUPABASE_PROJECT_PARAM)
    supabase_secret = aws.get_ssm_parameter(SUPABASE_SECRET_KEY_PARAM)
    
    logger.info(f"Creating Supabase user with {email}")
    characters = string.ascii_letters + string.digits
    temp_password = ''.join(random.choice(characters) for i in range(8))
    response = requests.post(
        f'https://{supabase_project}.supabase.co/auth/v1/admin/users', 
        headers={
            'Authorization': f"Bearer {supabase_secret}", 
            'apikey': supabase_api_key
        },
        json={
            "email": email,
            "password":  temp_password
        }
    )
    logger.info(f'Got response: {response.status_code}')
    
    return response.json()["id"], temp_password


def retrieve_payment_confirmation(checkout_session: str) -> dict:
    logger.info(f"Retrieving payment confirmation for session {checkout_session}")
    stripe.api_key = aws.get_ssm_parameter(STRIPE_API_KEY_PARAM)
    confirmation = stripe.checkout.Session.retrieve(checkout_session)
    logger.info(f"Payment confirmation: {confirmation}")
    return confirmation


@app.post("/members/v1/confirmation")
def confirmation():
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
            temp_password = add_member_with_temp_password(email)
            lead = aws.delete_ddb_item(
                table_name=LEADS_TABLE,
                key={"Email": email}
            )
            logger.info(f"Deleted lead: {lead}")
            response = {
                **response,
                **{
                    "status": confirmation["payment_status"],
                    "payment_type": payment_type,
                    "email": email,
                    "temp_password": temp_password,
                    "session_type": lead["Attributes"]["SessionType"],
                    "session_datetime": lead["Attributes"]["SessionDatetime"] 
                }
            }
        
        return response

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to confirm payment. Please contact us for assistance.")


@app.get("/members/v1/me")
def me():
    try:
        member = aws.get_ddb_item(
            table_name=MEMBERS_TABLE,
            key={"Email": app.current_event.get_query_string_value(name="email")}
        )
        logger.info(f"Retrieved member: {member}")

        return {"member": member}

    except Exception as e:
        logger.exception(e)
        raise BadRequestError("Failed to retrieve member details. Please contact us for assistance.")


@app.get("/members/v1/trial")
def trial():
    email = app.current_event.get_query_string_value(name="email")    
    member_exists = check_member_exists(email)

    if member_exists:
        logger.info(f"There is already a member with email {email}")
        redirect_url = f"{aws.get_ssm_parameter(TRIAL_ACTIVE_LINK_PARAM)}?email={email}"
    else:
        session_type = app.current_event.get_query_string_value(name="session_type")
        session_datetime = app.current_event.get_query_string_value(name="session_datetime")        
    
        logger.info(f"Creating a lead with {email} for session {session_type} on {session_datetime}")
        aws.put_ddb_item(
            table_name=LEADS_TABLE,
            params={
                "Item": {
                    "Email": email,
                    "LeadSource": "trial_session",
                    "SessionType": session_type,
                    "SessionDatetime": session_datetime,
                }
            }
        )
        redirect_url = f"{aws.get_ssm_parameter(TRIAL_PAYMENT_LINK_PARAM)}?prefilled_email={email}"
    
    logger.info(f"Redirecting to {redirect_url}")        
    return Response(
        status_code=301,
        headers={
            "Location": redirect_url,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": 0
        }
    )
        

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    return app.resolve(event, context)
