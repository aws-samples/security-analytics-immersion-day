import os
import json
import urllib.parse
import boto3
import gzip
import requests
from requests_aws4auth import AWS4Auth

s3 = boto3.client('s3')
es = boto3.client("es")
region = boto3.Session().region_name
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# configuration for OpenSearch request
domain = os.environ['OPENSEARCH_DOMAIN']
host = "https://" + es.describe_elasticsearch_domain(DomainName=domain)['DomainStatus']['Endpoint']
index = os.environ['OPENSEARCH_CLOUD_TRAIL_LOG_INDEX']
doc_type = '_doc'
url = f'{host}/{index}/{doc_type}'
header = {"Content-type": "application/json"}


def lambda_handler(event, context):
    # Get the object using the bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print(f'Loading trail logs for bucket: {bucket}, key: {key}')
    s3_object = s3.get_object(Bucket=bucket, Key=key)

    # decompress the object body and split into lines
    log_data = json.loads(gzip.decompress(s3_object['Body'].read()))

    successes = 0
    errors = 0

    for data in log_data['Records']:
        r = requests.post(url, auth=awsauth, json=data, headers=header)
        if r.ok:
            successes += 1
        else:
            errors += 1
            print(f"Response: {r}, {r.text}")

    print(f'Load complete. Successes: {successes}, Errors: {errors}')





