import os
import urllib.parse
import boto3
import gzip
import requests
from datetime import datetime
from requests_aws4auth import AWS4Auth

s3 = boto3.client('s3')
es = boto3.client('es')
region = boto3.Session().region_name
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# configuration for OpenSearch request
domain = os.environ['OPENSEARCH_DOMAIN']
index = os.environ['OPENSEARCH_VPC_FLOW_LOG_INDEX']
type = '_doc'
host = "https://" + es.describe_elasticsearch_domain(DomainName=domain)['DomainStatus']['Endpoint']
url = f'{host}/{index}/{type}'
header = {"Content-Type": "application/json"}

# vpc log field names
vpc_log_fields = ['version', 'account-id', 'interface-id', 'srcaddr', 'dstaddr', 'srcport', 'dstport', 'protocol',
                  'packets', 'bytes', 'start', 'end', 'action', 'log-status']


def lambda_handler(event, context):

    # Get the object using the bucket and key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    s3_object = s3.get_object(Bucket=bucket, Key=key)

    # decompress the object body and split into lines
    log_lines = gzip.decompress(s3_object['Body'].read()).splitlines()

    successes = 0
    errors = 0
    print(f'Loading vpc logs for bucket: {bucket}, key: {key}')

    # iterate over the lines, skipping the first line, which is a header
    # make the line a proper string by converting the line bytes to utf8
    # create a json doc by splitting the line into fields and mapping to field names
    # post the request and log an error response if it fails
    for line in log_lines[1:]:
        line = line.decode('utf8')

        line = {k: v for (k, v) in zip(vpc_log_fields, line.split())}
        line['start'] = datetime.fromtimestamp(int(line['start'])).strftime('%Y-%m-%d %H:%M:%S')
        line['end'] = datetime.fromtimestamp(int(line['end'])).strftime('%Y-%m-%d %H:%M:%S')
        print(line)
        r = requests.post(url, auth=awsauth, json=line, headers=header)
        if r.ok:
            successes += 1
        else:
            errors += 1
            print(f"Response: {r}, {r.text}")
    print(f'Load complete. Successes: {successes}, Errors: {errors}')




