import boto3
import json
import os
import requests
from datetime import datetime, timedelta
from requests_aws4auth import AWS4Auth

s3 = boto3.client('s3')
service = 'es'
region = boto3.Session().region_name
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)


def get_json(bucket, bucket_prefix, key):
    s3_object = s3.get_object(Bucket=bucket, Key=f'{bucket_prefix}{key}')
    data = s3_object['Body'].read()
    return json.loads(data)


def ichunk(a_list, size, end=0):
    '''
    iterate over a list in size chunks, starting at end
    '''
    while True:
        start = end
        end += size
        chunk = a_list[start:end]
        if len(chunk) == 0:
            return None
        yield chunk


def normalize_date(from_date_str, to_date, fmt='%Y-%m-%d'):
    """
    Set the date portion of start and end to a date
    We do this so that timestamps in the logfiles start on the to_date
    This keeps everything within a day for the lab
    """

    to_date_str = to_date.strftime(fmt)
    date_parts = from_date_str.split()
    to_date_str = f'{to_date_str} {date_parts[1]}'
    return to_date_str


def make_bulk_update_body(idx, lines):
    bulk = []
    for line in lines:
        bulk.append(f'{{ \"index\": {{ "_index": \"{idx}\" }} }}\n')
        bulk.append(json.dumps(line))
        bulk.append('\n')

    return ''.join(bulk)


def prepare_vpc_flow_index(data, set_date):
    prepped_data = []
    for line in data:
        # set date portion of time stamp to set_date, usually today - 1
        line['start'] = normalize_date(line['start'], set_date)
        line['end'] = normalize_date(line['end'], set_date)

        # enhance to simplify ip and port associations
        line['src_ip_port'] = f'{line["srcaddr"]}:{line["srcport"]}'
        line['dst_ip_port'] = f'{line["dstaddr"]}:{line["dstport"]}'

        prepped_data.append(line)

    return prepped_data


def prepare_cloud_trail_index(init_data, set_date):
    prepped_data = []
    for line in init_data:
        line['eventTime'] = normalize_date(line['eventTime'], set_date)
        prepped_data.append(line)

    return prepped_data


def bulk_update(bulk_data, host, idx, chunk_size):
    print(f'bulk_update {idx}')
    header = {"Content-Type": "application/json"}
    url = f'{host}/{idx}/_bulk'
    for next_n_lines in ichunk(bulk_data, chunk_size):
        bulk_chunk = make_bulk_update_body(idx, next_n_lines)
        r = requests.post(url, auth=awsauth, headers=header, data=bulk_chunk)
        err = json.loads(r.text)
        if err['errors']:
            print(err)
    return r


def init_log(host, index, bucket, bucket_prefix, mapping_name):
    print(f'create index {index} with mapping {mapping_name}')
    url = f'{host}/{index}'
    index_mapping = get_json(bucket, bucket_prefix, mapping_name)

    # delete the index if it exists
    r = requests.head(url, auth=awsauth)
    if r.ok:
        r = requests.delete(url, auth=awsauth)
        if not r.ok:
            print(r.text)

    # create the index with mapping
    r = requests.put(url, auth=awsauth, json=index_mapping)
    if not r.ok:
        print(r.text)
    return r


def lambda_handler(event, context):
    yesterday = datetime.today() - timedelta(days=1)
    es = boto3.client('es')

    domain = os.environ['OPENSEARCH_DOMAIN']
    bucket =os.environ['OPENSEARCH_INIT_BUCKET']
    bucket_prefix = os.environ['OPENSEARCH_INIT_BUCKET_PREFIX']
    chunk_size = os.getenv('CHUNK_SIZE', 500)
    cloud_trail_index = os.environ['OPENSEARCH_CLOUD_TRAIL_LOG_INDEX']
    cloud_trail_mapping = os.environ['OPENSEARCH_CLOUD_TRAIL_LOG_MAPPING']
    cloud_trail_sanitized = os.environ['OPENSEARCH_CLOUD_TRAIL_LOG_SANITIZED']
    vpc_flow_index = os.environ['OPENSEARCH_VPC_FLOW_LOG_INDEX']
    vpc_flow_mapping = os.environ['OPENSEARCH_VPC_FLOW_LOG_MAPPING']
    vpc_flow_sanitized = os.environ['OPENSEARCH_VPC_FLOW_LOG_SANITIZED']

    host = "https://" + es.describe_elasticsearch_domain(DomainName=domain)['DomainStatus']['Endpoint']

    print(f'opensearch-init-lambda for {yesterday}')

    init_log(host, cloud_trail_index, bucket, bucket_prefix, cloud_trail_mapping)
    bulk_data = prepare_cloud_trail_index(get_json(bucket, bucket_prefix, cloud_trail_sanitized), yesterday)
    bulk_update(bulk_data, host, cloud_trail_index, chunk_size)

    init_log(host, vpc_flow_index, bucket, bucket_prefix, vpc_flow_mapping)
    bulk_data = prepare_vpc_flow_index(get_json(bucket, bucket_prefix, vpc_flow_sanitized), yesterday)
    bulk_update(bulk_data, host, vpc_flow_index, chunk_size)


if __name__ == "__main__":
    awsauth=(os.environ['ESUSER'], os.environ['ESPASS'])
    lambda_handler({}, None)