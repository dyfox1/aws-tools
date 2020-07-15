import os
import json
import logging
import datetime

import boto3

LOG_LEVEL = os.environ['LOG_LEVEL']
DB_NAME = os.environ['DATABASE_NAME']
TBL_NAME = os.environ['TABLE_NAME']
REGION_NAME = os.environ['REGION']
LOOKBACK_HOURS = int(os.environ['LOOKBACK_HOURS'])
OUTPUT_LOCATION = os.environ['OUTPUT_LOCATION']

ATHENA_CLIENT = boto3.client('athena', region_name=REGION_NAME)

logger = logging.getLogger('partition-manager')
logger.setLevel(LOG_LEVEL.upper())

ALTER_TABLE_STATEMENT = """
ALTER TABLE {table_name} ADD IF NOT EXISTS
"""
PARTITION_STATEMENT = """
PARTITION ({partition_string})
"""

def iter_dates():
    """
    Iterates dates to populate partition string
    """
    now = datetime.datetime.utcnow()
    for i in range(LOOKBACK_HOURS):
        lookback_time = now - datetime.timedelta(hours=i)
        yield "year={year}, month={month}, day={day}, hour={hour}".format(
            year=str(lookback_time.year).zfill(4),
            month=str(lookback_time.month).zfill(2),
            day=str(lookback_time.day).zfill(2),
            hour=str(lookback_time.hour).zfill(2)
        )

def lambda_handler(event, context):
    """
    Builds query statement and executes the query
    via athena
    """
    query = ALTER_TABLE_STATEMENT.format(
        table_name=TBL_NAME
    )
    for partition_string in iter_dates():
        query += PARTITION_STATEMENT.format(
            partition_string=partition_string
        )
    
    ATHENA_CLIENT.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': DB_NAME
        },
        ResultConfiguration={
            'OutputLocation': OUTPUT_LOCATION
        })
