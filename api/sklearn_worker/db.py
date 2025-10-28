import sys
import psycopg2
import time
from psycopg2 import sql
from distutils.util import strtobool
import os, boto3, json, logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Load parameters at startup from SSM Parameter Store
AWS_REGION = os.environ.get('AWS_REGION')

def load_parameters():
    ssm = boto3.client('ssm', region_name=AWS_REGION)
    parameter_names = {
        '/steam-market-predictor/aws-secret-manager': 'AWS_SECRET_MANGER',
    }
    parameters = {}
    for param_name, env_key in parameter_names.items():
        try:
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            parameters[env_key] = response['Parameter']['Value']
        except ClientError as e:
            logger.error(f"Error loading parameter {param_name}: {e}")
    logger.info("Parameters loaded from SSM Parameter Store")
    logger.info(f"Loaded parameters: {list(parameters.keys())}")
    return parameters

def load_secret_manager():
    AWS_SECRET_MANGER = load_parameters().get('AWS_SECRET_MANGER')
    client = boto3.client('secretsmanager', region_name=AWS_REGION)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=AWS_SECRET_MANGER)
        secret_string = get_secret_value_response['SecretString']
        
        # Parse the secret string as JSON
        secret_data = json.loads(secret_string)
        
        logger.info("Secrets loaded from AWS Secrets Manager")
        logger.info(f"Loaded secrets: {list(secret_data.keys())}")
        return secret_data
    except ClientError as e:
        logger.error(f"Error loading secret {AWS_SECRET_MANGER}: {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing secret JSON: {e}")
        return {}

secrets = load_secret_manager()
if secrets:
    os.environ["DB_USER"] = secrets.get("DB_USER")
    os.environ["DB_PASSWORD"] = secrets.get("DB_PASSWORD")

DB_HOST = "database-1-instance-1.ce2haupt2cta.ap-southeast-2.rds.amazonaws.com"
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = "cohort_2025"
DB_PORT = 5432
DB_SCHEMA = os.environ.get("DB_SCHEMA", DB_USER)

# Reset database option
RESET_DATABASE = bool(strtobool(os.environ.get("RESET_DATABASE", "False")))

# Get a connection to the database, retry 10 times
def get_connection():
    for attempt in range(10):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                sslmode='require'
            )
            # Set schema for isolation
            cursor = conn.cursor()
            cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(DB_SCHEMA)))
            conn.commit()
            cursor.close()
            return conn
        except psycopg2.Error as e:
            print(f"Attempt {attempt+1}/10: Error connecting to PostgreSQL: {e}")
            time.sleep(3)
    print("Failed to connect to PostgreSQL after 10 attempts. Exiting.")
    sys.exit(1)

# Set the has_model flag for a group
def model_set_group_has_ml(conn: psycopg2.extensions.connection, group_id: int, has_model: bool):
    cursor = conn.cursor()
    cursor.execute("UPDATE groups SET has_model = %s WHERE id = %s", (has_model, group_id))
    conn.commit()

# Save a new model index into the database
def model_save_ml_index(user_id: int, group_id: int, item_id: int, data_hash: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO model_index (user_id, group_id, item_id, data_hash)
        VALUES (%s, %s, %s, %s)
    """, (user_id, group_id, item_id, data_hash))
    cursor.execute("SELECT LASTVAL()")
    model_id = cursor.fetchone()[0]
    conn.commit()
    model_set_group_has_ml(conn, group_id, True)
    cursor.close()
    conn.close()
    return {
        "id": model_id,
        "user_id": user_id,
        "group_id": group_id,
        "item_id": item_id,
        "data_hash": data_hash,
    }