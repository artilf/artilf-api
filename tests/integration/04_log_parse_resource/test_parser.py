import json
from gzip import GzipFile
from io import BytesIO
from time import sleep

import pytest


@pytest.fixture(scope='function')
def fixture(s3, sqs, stack_outputs):
    bucket = stack_outputs['DummyBucketName']
    key = '1223334444'

    expected = {
        'logGroup': 'test_group',
        'logStream': 'test_stream',
        'datetime': '2019-02-26 10:33:26.145000+09:00',
        'message': '{"levelname": "ERROR", "lambda_request_id": "test_id"}',
        'request_id': 'test_id'
    }

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
        })
    ])

    io = BytesIO()
    GzipFile(fileobj=io, mode='wb').write(json.dumps(gz_body).encode())

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=io.getvalue()
    )

    event = {
        's3': {
            'bucket': {'name': 'test_bucket'},
            'object': {'key': '1223334444'}
        }
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

    sleep(30)

    resp = sqs.receive_message(
        QueueUrl=receive_queue_url,
        MaxNumberOfMessages=1
    )
    record = resp['Messages'][0]
    sqs.delete_message(
        QueueUrl=receive_queue_url,
        ReceiptHandle=record['ReceiptHandle']
    )
    raw_body = json.loads(record['Body'])
    body = json.loads(raw_body['Message'])

    assert body == expected
