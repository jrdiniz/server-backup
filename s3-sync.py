import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv
load_dotenv()

# Determine full logging file path
abspath = os.path.abspath(os.path.dirname(__file__))

def upload_directory_to_s3(local_dir, bucket_name, s3_prefix=""):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('AWS_ENDPOINT_URL'),
        region_name='auto'
    )

    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = os.path.join(s3_prefix, relative_path).replace("\\", "/")

            try:
                print(f"Uploading {local_path} to s3://{bucket_name}/{s3_path}")
                s3.upload_file(local_path, bucket_name, s3_path)
            except NoCredentialsError:
                print("Credentials not available")
                return

# Example usage:
upload_directory_to_s3(
    local_dir="/home/juliano/scripts/server-backup/teste",
    bucket_name="gorobei",
    s3_prefix=""  # or "" for root
)