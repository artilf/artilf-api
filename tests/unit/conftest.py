import os
from gzip import GzipFile
from io import BytesIO
from uuid import uuid4

import boto3
import pytest

os.environ['Env'] = 'development'


class DummyContext(object):
    def __init__(self, request_id):
        self.aws_request_id = request_id


@pytest.fixture(scope='session')
def s3():
    return boto3.client('s3', endpoint_url='http://localhost:4572')


@pytest.fixture(scope='session')
def s3_resource():
    return boto3.resource('s3', endpoint_url='http://localhost:4572')


@pytest.fixture(scope='session')
def sqs():
    return boto3.client('sqs', endpoint_url='http://localhost:4576')


@pytest.fixture(scope='function')
def dummy_context(request):
    return DummyContext(request.param)


@pytest.fixture(scope='function')
def delete_environ(request):
    yield
    for key in request.param:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope='function')
def set_environ(request):
    previous = {}
    for k, v in request.param.items():
        previous[k] = os.environ.get(k)
        os.environ[k] = v

    yield

    for k, v in previous.items():
        if v is None:
            del os.environ[k]
        else:
            os.environ[k] = v


@pytest.fixture(scope='function')
def create_s3_bucket(s3_resource, request):
    s3_resource.create_bucket(Bucket=request.param)
    yield
    bucket = s3_resource.Bucket(request.param)
    bucket.objects.all().delete()
    bucket.delete()


@pytest.fixture(scope='function')
def s3_put_gz_files(request, s3):
    for param in request.param['objects']:
        io = BytesIO()

        with GzipFile(fileobj=io, mode='wb') as f:
            f.write(param['body'].encode())

        s3.put_object(
            Bucket=request.param['bucket'],
            Key=param['key'],
            Body=io.getvalue()
        )


@pytest.fixture(scope='function')
def create_sqs_queue(sqs):
    queue_name = str(uuid4())
    resp = sqs.create_queue(QueueName=queue_name)
    url = resp['QueueUrl']
    yield url
    sqs.delete_queue(QueueUrl=url)
