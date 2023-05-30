#!/bin/bash

pip3 install -t python -r requirements.txt
zip -r opensearch-lambda-layer.zip python
zip cloud-trail-log-to-opensearch.zip cloud-trail-log-to-opensearch.zip
zip vpc-flow-log-to-opensearch.zip vpc-flow-log-to-opensearch.py
zip opensearch-init-lambda.zip opensearch-init-lambda.py