from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
import boto3, joblib, json, io, os

BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
REGION_NAME = os.environ.get('AWS_REGION')

class S3StorageManager:
    """
    S3-based storage manager for ML model artifacts and temporary files.
    """

    def __init__(self):
        """
        Initialize S3 client and bucket configuration.
        """
        self.bucket_name = BUCKET_NAME

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=REGION_NAME,
            )
            self.s3_client.list_buckets()
            print(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            print(f"Failed to initialize S3 client: {e}")
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
            print(f"File uploaded to s3://{self.bucket_name}/{file_key}")
            return True
        except ClientError as e:
            print(f"Failed to upload file to S3: {e}")
            return False

    def download_file(self, file_key: str, data_type: str = 'bytes') -> Optional[Any]:
        """
        Generic download method. Specify data_type: 'json' (returns dict), 'model' (returns object), 'bytes' (default, returns bytes).
        """
        if not self.s3_client:
            return None

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            print(f"File downloaded from s3://{self.bucket_name}/{file_key}")
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
            print(f"Failed to download file from S3: {e}")
            return None

    # TODO: IMPLEMENT FOR S3 urls
    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in S3.
        """
        if not self.s3_client:
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False

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
            print(f"Failed to generate presigned URL: {e}")
            return None

    def generate_upload_url(self, file_key: str, content_type: str = None, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for uploading files to S3.
        """
        if not self.s3_client:
            return None

        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': file_key
            }

            if content_type:
                params['ContentType'] = content_type

            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Failed to generate upload URL: {e}")
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
            print(f"File deleted from s3://{self.bucket_name}/{file_key}")
            return True
        except ClientError as e:
            print(f"Failed to delete file from S3: {e}")
            return False

    # UNUSED
    def list_files(self, prefix: str = "") -> list:
        """
        List files in the S3 bucket with optional prefix.
        """
        if not self.s3_client:
            return []

        try:
            files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
            return files
        except ClientError as e:
            print(f"Failed to list files in S3: {e}")
            return []