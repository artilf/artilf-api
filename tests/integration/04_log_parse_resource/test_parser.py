import json
from gzip import GzipFile
from io import BytesIO


def test_normal(s3, sqs, stack_outputs):
    bucket = stack_outputs['DummyBucketName']
    key = '1223334444'

    body = '\n'.join([
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
    GzipFile(fileobj=io, mode='wb').write(json.dumps(body).encode())

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=io.getvalue()
    )
