from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routes import router_items, router_users, router_steam
import uvicorn, os, boto3

from botocore.exceptions import ClientError

# Load secrets at startup
def load_secrets():
    ssm = boto3.client('ssm', region_name='ap-southeast-2')
    try:
        response = ssm.get_parameters_by_path(
            Path='/steam-market-predictor/',
            Recursive=True,
            WithDecryption=True
        )
        # Map parameter names to expected env var names
        key_mapping = {
            'redis-host': 'REDIS_HOST',
            's3-bucket-name': 'S3_BUCKET_NAME',
            'steam-com-base': 'STEAM_COM_BASE',
            'steam-api-base': 'STEAM_API_BASE',
        }
        secrets = {key_mapping.get(param['Name'].split('/')[-1], param['Name'].split('/')[-1]): param['Value'] for param in response['Parameters']}
        return secrets
    except ClientError as e:
        print(f"Error loading secrets: {e}")
        return {}
    
secrets = load_secrets()
os.environ.update(secrets)

# Initialize APIno
SITE_PORT = os.environ.get("SITE_PORT")

app = FastAPI(
    title="Steam Market Price Predictor API",
    description="API for predicting Steam market item prices",
    version="1.0.0",
)

# Prefix is used to group routes under a common path
app.include_router(router_items, prefix="/group")
app.include_router(router_steam, prefix="/steam")
app.include_router(router_users, prefix="/users")

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=SITE_PORT)