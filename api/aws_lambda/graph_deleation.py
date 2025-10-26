import boto3
import os

def lambda_handler(event, context):
    bucket = os.environ.get("S3_BUCKET_NAME")
    keep_count = int(os.environ.get("KEEP_COUNT", "10"))
    if not bucket:
        return {"statusCode": 500, "body": "Missing S3_BUCKET_NAME env var"}

    s3 = boto3.client("s3")
    prefix = "predictions/"
    objects = []
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            objects.append(obj)
    objects.sort(key=lambda x: x["LastModified"], reverse=True)

    deleted = []
    for obj in objects[keep_count:]:
        key = obj["Key"]
        s3.delete_object(Bucket=bucket, Key=key)
        deleted.append(key)

    return {
        "statusCode": 200,
        "body": f"Deleted {len(deleted)} objects: {deleted}"
    }