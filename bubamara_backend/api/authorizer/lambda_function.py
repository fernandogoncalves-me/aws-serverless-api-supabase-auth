import os
import requests

from aws_lambda_powertools import Logger

from bubamara_backend.libs.aws import AWS

SUPABASE_PROJECT_PARAM = os.environ['SUPABASE_PROJECT_PARAM']
SUPABASE_API_KEY_PARAM = os.environ['SUPABASE_API_KEY_PARAM']

aws = AWS()
logger = Logger()

def lambda_handler(event, _):
    token = event['headers'].get('authorization', '')
    supabase_project = aws.get_ssm_parameter('SUPABASE_PROJECT_PARAM')
    supabase_api_key = aws.get_ssm_parameter('SUPABASE_API_KEY_PARAM')
    response = requests.get(
        f'https://${supabase_project}.supabase.co/auth/v1/user', 
        headers={
            'Authorization': token, 
            'apikey': supabase_api_key
        }
    )
    logger.info(f'Got response: {response.status_code}')

    if response.status_code == 200:
        return generate_policy('user', 'Allow', event['routeArn'])
    else:
        return generate_policy('user', 'Deny', event['routeArn'])

def generate_policy(principal_id, effect, resource):
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    return policy
