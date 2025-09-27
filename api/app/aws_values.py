import os, boto3, json
from botocore.exceptions import ClientError

# Load parameters at startup from SSM Parameter Store
AWS_REGION = os.environ.get('AWS_REGION')
AWS_SECRET_MANGER = os.environ.get('AWS_SECRET_MANGER')
def load_parameters():
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    parameter_names = {
        '/steam-market-predictor/s3-bucket-name': 'S3_BUCKET_NAME',
        '/steam-market-predictor/steam-com-base': 'STEAM_COM_BASE',
        '/steam-market-predictor/steam-api-base': 'STEAM_API_BASE',
        '/steam-market-predictor/cognito-domain': 'COGNITO_DOMAIN',
        '/steam-market-predictor/aws-secret-manager': 'AWS_SECRET_MANGER',
    }
    parameters = {}
    for param_name, env_key in parameter_names.items():
        try:
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            parameters[env_key] = response['Parameter']['Value']
        except ClientError as e:
            print(f"Error loading parameter {param_name}: {e}")
    print("Parameters loaded from SSM Parameter Store")
    print("Loaded parameters:", parameters)
    return parameters

def load_secret_manager():
    client = boto3.client('secretsmanager', region_name=AWS_REGION)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=AWS_SECRET_MANGER)
        secret_string = get_secret_value_response['SecretString']
        
        # Parse the secret string as JSON
        secret_data = json.loads(secret_string)
        
        print("Secrets loaded from AWS Secrets Manager")
        print("Loaded secrets:", list(secret_data.keys()))
        return secret_data
    except ClientError as e:
        print(f"Error loading secret {AWS_SECRET_MANGER}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing secret JSON: {e}")
        return {}