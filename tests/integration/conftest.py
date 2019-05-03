import pytest
import botocore.session

from botocore import credentials
import pathlib
import boto3
import os


def get_service_object(name, botocore_session, is_resource=False):
    session = None
    if os.getenv('CIRCLECI'):
        session = boto3
    else:
        session = boto3.Session(botocore_session=botocore_session, profile_name=os.environ['AWS_PROFILE'])

    if is_resource:
        return session.resource(name)
    else:
        return session.client(name)


@pytest.fixture(scope='session')
def botocore_session():
    cache_dir = str(pathlib.Path.home().joinpath('.aws/cli/cache'))

    session = botocore.session.get_session()
    provider = session.get_component('credential_provider').get_provider('assume-role')
    provider.cache = credentials.JSONFileCache(cache_dir)

    return session


@pytest.fixture(scope='session')
def cfn(botocore_session):
    return get_service_object('cloudformation', botocore_session)


@pytest.fixture(scope='session')
def s3(botocore_session):
    return get_service_object('s3', botocore_session)


@pytest.fixture(scope='session')
def sqs(botocore_session):
    return get_service_object('sqs', botocore_session)


@pytest.fixture(scope='session')
def stack_info(stack_name, cfn):
    resp = cfn.describe_stacks(StackName=stack_name)
    return resp['Stacks'][0]


@pytest.fixture(scope='session')
def stack_outputs(stack_info):
    result = {}
    for item in stack_info['Outputs']:
        result[item['OutputKey']] = item['OutputValue']
    return result
