## Security Analytics Immersion Day

This repository contains the files necessary to run the **Security Analytics Immersion Day** in a non-AWS Workshop event account.  If you are running in an AWS Workshop event, then an AWS account is provisioned for you and these files are automatically made available via the workshop S3 asset bucket.  If you are running this workshop in another account, for example in your personal account or a company account, then you will need to provision these files by following the instructions here.

## Prerequisites

You will need access to the following:
1. An AWS account where you will install the workshop
2. A Linux or Unix workstation with the AWS CLI installed
3. An S3 bucket and folder where you will host files packaged from this repository

## Setup

1. If necessary create a bucket and folder to host the files that will be created from the steps that follow
2. Open a command line window and create or navigate to a directory where you want to clone this repository and execute the following commands
~~~
git clone https://github.com/aws-samples/security-analytics-immersion-day.git
cd aws-samples/security-analytics-immersion-day
bash build.sh

# In the following command, use the bucket name and folder path you chose to use or created above
aws s3 sync ./s3 s3://<your-bucket-name>/<your-folder-path>
~~~
3. Open the AWS Console and navigate to CloudFormation
4. Select **Create stack**
5. In the **Specify template** section, enter the following S3 URL
~~~
https://<your-bucket-name>.s3.amazonaws.com/<your-folder-path>/cloudformation.yaml
~~~
6. Click **Next**
7. Enter a **Stack name**
8. Enter _your-bucket-name_ in the **WSAssetBucketName** field
9. Enter _your-folder-path/_ in the **WSAssetBucketPrefix**

**IMPORTANT** make sure the folder path ends with a '/' character
10. Click **Next**
11. No changes are required on **Configure stack options**, Click **Next**
12. Review the stack, scroll to the bottom of the page and click the checkbox acknowledging the creation of IAM resources, and click **Next**
13. The stack will be created.

When stack creation completes you can follow the steps in Workshop documentation for **Module-3: Analyze Logs with OpenSearch**

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

test git defender
