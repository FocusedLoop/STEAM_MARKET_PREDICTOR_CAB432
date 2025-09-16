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

    def upload_model_or_scaler(self, model_object: Any, model_key: str) -> bool:
        """
        Upload a trained model to S3.
        """
        if not self.s3_client:
            return False

        try:
            # Serialize model to bytes
            buffer = io.BytesIO()
            joblib.dump(model_object, buffer)
            buffer.seek(0)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=model_key,
                Body=buffer.getvalue(),
                ContentType='application/octet-stream'
            )
            print(f"Model uploaded to s3://{self.bucket_name}/{model_key}")
            return True
        except ClientError as e:
            print(f"Failed to upload model to S3: {e}")
            return False

    def download_model_or_scaler(self, model_key: str) -> Optional[Any]:
        """
        Download a trained model from S3.
        """
        if not self.s3_client:
            return None

        try:
            # Download from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=model_key
            )

            # Deserialize model
            buffer = io.BytesIO(response['Body'].read())
            model = joblib.load(buffer)
            print(f"Model downloaded from s3://{self.bucket_name}/{model_key}")
            return model
        except ClientError as e:
            print(f"Failed to download model from S3: {e}")
            return None

    def upload_json_data(self, data: Dict[str, Any], json_key: str) -> bool:
        """
        Upload JSON data to S3.
        """
        if not self.s3_client:
            return False

        try:
            # Serialize to JSON string
            json_string = json.dumps(data, indent=2)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=json_key,
                Body=json_string,
                ContentType='application/json'
            )
            print(f"JSON data uploaded to s3://{self.bucket_name}/{json_key}")
            return True
        except ClientError as e:
            print(f"Failed to upload JSON to S3: {e}")
            return False

    def download_json_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Download JSON data from S3.
        """
        if not self.s3_client:
            return None

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response['Body'].read().decode('utf-8')
            print(f"JSON data downloaded from s3://{self.bucket_name}/{key}")
            return json.loads(data)
        except ClientError as e:
            print(f"Failed to download JSON from S3: {e}")
            return None

    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.
        """
        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            print(f"File deleted from s3://{self.bucket_name}/{file_key}")
            return True
        except ClientError as e:
            print(f"Failed to delete file from S3: {e}")
            return False

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