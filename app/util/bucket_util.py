import boto3

def upload_to_s3(local_path, bucket, key):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"

def download_from_s3(bucket, key, local_path):
    s3 = boto3.client('s3')
    s3.download_file(bucket, key, local_path)