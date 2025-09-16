import os, boto3
from botocore.exceptions import ClientError

# Load parameters at startup from SSM Parameter Store
AWS_REGION = os.environ.get('AWS_REGION')
def load_parameters():
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    parameter_names = {
        '/steam-market-predictor/s3-bucket-name': 'S3_BUCKET_NAME',
        '/steam-market-predictor/steam-com-base': 'STEAM_COM_BASE',
        '/steam-market-predictor/steam-api-base': 'STEAM_API_BASE',
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