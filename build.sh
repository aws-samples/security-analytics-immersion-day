#!/bin/bash

rm -rf python/*
pip3 install -t python -r requirements.txt
zip -r s3/opensearch-lambda-layer.zip python
zip s3/cloud-trail-log-to-opensearch.zip cloud-trail-log-to-opensearch.py
zip s3/vpc-flow-log-to-opensearch.zip vpc-flow-log-to-opensearch.py
zip s3/opensearch-init-lambda.zip opensearch-init-lambda.py