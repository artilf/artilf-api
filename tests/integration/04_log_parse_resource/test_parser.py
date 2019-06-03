import json
import os
from gzip import GzipFile
from io import BytesIO
from time import sleep

import pytest


def get_wait_second():
    result = 60
    try:
        result = int(os.environ['ITG_WAIT_SECOND'])
    except Exception:
        pass
    return result


@pytest.fixture(scope='function')
def fixture(s3, sqs, stack_outputs):
    bucket = stack_outputs['DummyBucketName']
    key = '1223334444'

    expected = [
        {
            'logGroup': 'test_group',
            'logStream': 'test_stream',
            'datetime': '2019-02-26 10:33:26.145000+09:00',
            'message': '{"levelname": "ERROR", "lambda_request_id": "test_id"}',
            'request_id': 'test_id'
        },
        {
            'logGroup': 'test_group_2',
            'logStream': 'test_stream',
            'datetime': '2019-03-01 21:53:26.145000+09:00',
            'message': '{"levelname": "ERROR", "lambda_request_id": "test_id_ttt"}',
            'request_id': 'test_id_ttt'
        }
    ]

    gz_body = '\n'.join([
        json.dumps({
            'logGroup': 'test_group',
            'logStream': 'test_stream',
            'logEvents': [
                {
                    'timestamp': 1551144806145,
                    'message': '{"levelname": "ERROR", "lambda_request_id": "test_id"}'
                }
            ]
        }),
        json.dumps({
            'logGroup': 'test_group_2',
            'logStream': 'test_stream',
            'logEvents': [
                {
                    'timestamp': 1551444806145,
                    'message': '{"levelname": "ERROR", "lambda_request_id": "test_id_ttt"}'
                }
            ]
        })
    ])

    io = BytesIO()
    GzipFile(fileobj=io, mode='wb').write(gz_body.encode())

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=io.getvalue()
    )

    event = {
        'Records': [
            {
                's3': {
                    'bucket': {'name': bucket},
                    'object': {'key': key}
                }
            }
        ]
    }

    yield (event, expected)

    s3.delete_object(
        Bucket=bucket,
        Key=key
    )


def test_normal(sqs, sns, stack_outputs, fixture):
    s3_event_topic_arn = stack_outputs['S3EventTopicArn']
    receive_queue_url = stack_outputs['DummyReceiveQueueUrl']
    event, expected = fixture

    sns.publish(
        TopicArn=s3_event_topic_arn,
        Message=json.dumps(event)
    )

    sleep(get_wait_second())

    actual = []

    for _ in range(2):
        resp = sqs.receive_message(
            QueueUrl=receive_queue_url,
            MaxNumberOfMessages=1
        )
        for record in resp['Messages']:
            sqs.delete_message(
                QueueUrl=receive_queue_url,
                ReceiptHandle=record['ReceiptHandle']
            )
            raw_body = json.loads(record['Body'])
            body = json.loads(raw_body['Message'])
            actual.append(body)

    assert {x['logGroup']: x for x in actual} == {x['logGroup']: x for x in expected}
