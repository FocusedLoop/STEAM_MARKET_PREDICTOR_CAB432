from typing import Optional, Any
from botocore.exceptions import ClientError
import boto3, joblib, json, io, os, logging

logger = logging.getLogger(__name__)

REGION_NAME = os.environ.get('AWS_REGION')

def load_bucket_name_from_ssm():
    ssm = boto3.client('ssm', region_name=REGION_NAME)
    param_name = '/steam-market-predictor/s3-bucket-name'
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        bucket_name = response['Parameter']['Value']
        logger.info(f"Loaded S3 bucket name from SSM: {bucket_name}")
        return bucket_name
    except ClientError as e:
        logger.error(f"Error loading S3 bucket name from SSM: {e}")
        return None

class S3StorageManager:
    """
    S3-based storage manager for ML model artifacts and temporary files.
    """

    def __init__(self):
        """
        Initialize S3 client and bucket configuration.
        """
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            bucket_name = load_bucket_name_from_ssm()
        self.bucket_name = bucket_name

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=REGION_NAME,
            )
            self.s3_client.list_buckets()
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.info(f"Failed to initialize S3 client: {e}")
            self.s3_client = None

    def upload_file(self, data: Any, file_key: str, data_type: str = 'bytes') -> bool:
        """
        Generic upload method for files (JSON dict, PNG bytes, models/scalers, etc.).
        Serializes data based on type if needed.
        """
        if not self.s3_client:
            return False

        try:
            if data_type == 'json':
                body = json.dumps(data, indent=2)
                content_type = 'application/json'
            elif data_type == 'model':
                buffer = io.BytesIO()
                joblib.dump(data, buffer)
                buffer.seek(0)
                body = buffer.getvalue()
                content_type = 'application/octet-stream'
            elif data_type == 'bytes':
                body = data
                content_type = 'application/octet-stream'
            else:
                raise ValueError("Invalid data_type specified. Use 'json', 'model', or 'bytes'.")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=body,
                ContentType=content_type
            )
            logger.info(f"File uploaded to s3://{self.bucket_name}/{file_key}")
            return True
        except ClientError as e:
            logger.warning(f"Failed to upload file to S3: {e}")
            return False

    def download_file(self, file_key: str, data_type: str = 'bytes') -> Optional[Any]:
        """
        Generic download method. Specify data_type: 'json' (returns dict), 'model' (returns object), 'bytes' (default, returns bytes).
        """
        if not self.s3_client:
            return None

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File downloaded from s3://{self.bucket_name}/{file_key}")
            data = response['Body'].read()

            if data_type == 'json':
                data = data.decode('utf-8')
                return json.loads(data)
            elif data_type == 'model':
                buffer = io.BytesIO(data)
                return joblib.load(buffer)
            elif data_type == 'bytes':
                return data
            else:
                raise ValueError("Invalid data_type specified. Use 'json', 'model', or 'bytes'.")

        except ClientError as e:
            logger.warning(f"Failed to download file from S3: {e}")
            return None

    def generate_presigned_url(self, file_key: str, operation: str = 'get_object', expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for S3 operations.
        """
        if not self.s3_client:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.warning(f"Failed to generate presigned URL: {e}")
            return None

    def generate_download_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading files from S3.
        """
        return self.generate_presigned_url(file_key, 'get_object', expiration)
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.
        """
        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted from s3://{self.bucket_name}/{file_key}")
            return True
        except ClientError as e:
            logger.warning(f"Failed to delete file from S3: {e}")
            return False