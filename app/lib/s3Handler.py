import boto3
import properties

# Use this for development with fake S3
s3 = boto3.client('s3', endpoint_url='http://'+properties.S3_ENDPOINT_HOST+':4569', aws_access_key_id="", aws_secret_access_key="")

# Use this when run in AWS
# s3 = boto3.client('s3')

def s3_put(key, file):
    s3.put_object(Body=file,ContentType=file.content_type,Bucket=properties.S3_BUCKET_NAME,Key=key)


def s3_get(filename):
    obj = s3.get_object(Bucket=properties.S3_BUCKET_NAME, Key=filename)
    return obj


def s3_delete(filename):
    s3.delete_object(Bucket=properties.BUCKET_NAME, Key=filename)

