import json
import os
from datetime import datetime, timedelta, timezone
from gzip import GzipFile
from json import JSONDecoder
from json.decoder import WHITESPACE

import boto3

from logger.get_logger import get_logger

logger = get_logger(__name__)
decoder = JSONDecoder()


def main(event, client_s3=boto3.client('s3'), client_sns=boto3.client('sns')):
    logger.info('event', event)
    topic_arn = os.environ.get('LOG_ALERT_TOPIC_ARN')
    s3_objects = validate_and_get_s3_object_info(event, topic_arn)
    alerts = []
    for s3_object in s3_objects:
        log_data = get_log_data(s3_object, client_s3)
        alerts += parse_log_data(log_data)
    publish(alerts, topic_arn, client_sns)


def validate_and_get_s3_object_info(event, topic_arn):
    if not isinstance(topic_arn, str):
        raise TypeError('topic_arn is not string.')
    if len(topic_arn) == 0:
        raise ValueError('topic_arn is empty string.')

    result = []
    for i, record in enumerate(event['Records']):
        try:
            option = {
                'Bucket': record['s3']['bucket']['name'],
                'Key': record['s3']['object']['key']
            }
            for k, v in option.items():
                if not isinstance(v, str):
                    raise TypeError(f'{k} is not string.')
                if len(v) == 0:
                    raise ValueError(f'{k} is empty string.')
            result.append(option)
        except Exception as e:
            logger.warning(f'Exception occurred in event["Records"][{i}]: {e}')
            raise

    return result


def json_iter_load(text):
    size = len(text)
    index = 0
    while index < size:
        obj, offset = decoder.raw_decode(text, index)
        yield obj
        search = WHITESPACE.search(text, offset)
        if search is None:
            break
        index = search.end()


def get_log_data(s3_object, s3_client):
    resp = s3_client.get_object(**s3_object)
    binary = GzipFile(fileobj=resp['Body']).read()
    return list(json_iter_load(binary.decode()))


def parse_log_data(log_data):
    result = []
    for log in log_data:
        for event in log['logEvents']:
            if '"levelname": "ERROR"' in event['message']:
                alert = {
                    'logGroup': log['logGroup'],
                    'logStream': log['logStream'],
                    'datetime': str(datetime.fromtimestamp(event['timestamp']/1000, timezone(timedelta(hours=+9)))),
                    'message': event['message'],
                    'request_id': None
                }
                try:
                    message_json = json.loads(event['message'])
                    alert['request_id'] = message_json['lambda_request_id']
                except Exception:
                    pass
                result.append(alert)
    return result


def publish(alerts, topic_arn, sns):
    for alert in alerts:
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(alert)
        )
