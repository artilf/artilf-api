import json
import os
from urllib.parse import quote

from aws_sns_to_slack import slack_notify
from logger.get_logger import get_logger

logger = get_logger(__name__)


def main(event):
    logger.info('event', event)
    errors = validate_and_get(event)
    publish(errors)


def validate_and_get(event):
    result = []
    if not isinstance(event, dict):
        raise TypeError('event is not dict.')
    records = event.get('Records')
    if not isinstance(records, list):
        raise TypeError('event["Records"] is not list.')
    for i, record in enumerate(records):
        logger.info(f'event["Records"][{i}]', record)
        if not isinstance(record, dict):
            raise TypeError(f'event["Records"][{i}] is not dict')
        body = record.get('body')
        result.append(json.loads(body))
    return result


def publish_error(error):
    log_group = error['logGroup']
    log_stream = error['logStream']
    date = error['datetime']
    message = error['message']
    request_id = error['request_id']

    url = (
        f'https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home'
        f'?region=ap-northeast-1#logEventViewer:group={log_group};stream={quote(log_stream)}'
    )

    if request_id is not None:
        url += quote(f';filter="{request_id}"')

    function_name = os.path.basename(log_group)
    lines = [
        f'Function: {function_name}',
        f'Datetime: {date}',
        f'URL: {url}',
        f'LogGroup: {log_group}',
        f'LogStream: {log_stream}',
        f'RequestId: {request_id}',
        f'Message:',
        f'```',
        message,
        f'```'
    ]
    option = {
        'username': date,
        'text': '\n'.join(lines),
        'icon_emoji': ':warning:'
    }
    slack_notify(json.dumps(option))


def publish(errors):
    for error in errors:
        publish_error(error)
