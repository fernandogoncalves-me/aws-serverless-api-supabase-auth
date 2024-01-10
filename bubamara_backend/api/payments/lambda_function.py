import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig, Response
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
import stripe

from libs.aws import AWS


STRIPE_API_KEY_PARAM = os.environ["STRIPE_API_KEY_PARAM"]
ALLOW_ORIGIN = os.environ["ALLOW_ORIGIN"]

aws = AWS()
cors_config = CORSConfig(allow_origin=ALLOW_ORIGIN)
app = APIGatewayHttpResolver(cors=cors_config)
logger = Logger()


@app.post("/confirmation")
def payment_confirmation():
    try:
        checkout_session = app.current_event.get_query_string_value("cs")
        confirmation = stripe.checkout.Session.retrieve(checkout_session)
        logger.info(confirmation)

        if confirmation["payment_status"] != "paid":
            return Response(status_code=400, body={"message": "Payment not completed."})
        else:
            return Response(status_code=200, body={"message": "Payment completed."})

    except Exception as e:
        logger.exception(e)
        return {"message": "Failed to retrieve payment confirmation"}, 500


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    stripe.api_key = aws.get_ssm_parameter(STRIPE_API_KEY_PARAM)
    return app.resolve(event, context)
