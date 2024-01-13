import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger

from bubamara_backend.libs.aws import AWS


MEMBERS_TABLE = os.environ["MEMBERS_TABLE"]

app = APIGatewayHttpResolver()
aws = AWS()
logger = Logger()


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

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Got request: {event}")
    return app.resolve(event, context)
