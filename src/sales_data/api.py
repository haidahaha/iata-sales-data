import logging
import os
import io
import boto3
import requests
import pandas as pd
import awswrangler as wr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESOURCE = 'sales_data'
URL = 'https://eforexcel.com/wp/wp-content/uploads/2020/09/2m-Sales-Records.zip'
S3_ORIGINAL_FILENAME = 'original-2m-Sales-Records.zip'
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'iata-sales-data-lake')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'salesdata')
TABLE_NAME = DATABASE_NAME

def lambda_handler(event, context):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    try:    
        response = requests.get(URL, headers=headers)
    except Exception as e:
        logger.error({
          'resource': RESOURCE,
          'operation': 'fetch raw sales data',
          'error': str(e)
        })
        raise e
    
    data = response.content

    try:
        s3 = boto3.client("s3") 
        s3.put_object(Bucket=BUCKET_NAME, Key=S3_ORIGINAL_FILENAME, Body=data)
    except Exception as e:
        logger.error({
          'resource': RESOURCE,
          'operation': 'save raw sales data to s3',
          'error': str(e)
        })

    try:
        df = pd.read_csv(io.BytesIO(data))

        wr.s3.to_parquet(
            df=df,
            path=f"s3://{BUCKET_NAME}/rawsalesdata/",
            dataset=True,
            database=DATABASE_NAME,
            table=TABLE_NAME,
            partition_cols=['Country']
        )

    except Exception as e:
        logger.error({
          'resource': RESOURCE,
          'operation': 'fetch sales data',
          'error': str(e)
        })