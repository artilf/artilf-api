import os

import pytest

from logger.aws_lambda_tools import save_request_id


@save_request_id
def dummy_handler(event, context):
    pass


@pytest.mark.parametrize(
    'delete_environ', [
        (
            ['LAMBDA_REQUEST_ID']
        )
    ], indirect=True
)
@pytest.mark.usefixtures('delete_environ')
class TestSaveRequestId(object):
    @pytest.mark.parametrize(
        'dummy_context, request_id', [
            (
                'e216c232-0b1f-4590-bec0-a0ff937857d0',
                'e216c232-0b1f-4590-bec0-a0ff937857d0'
            ),
            (
                '80e13f4a-6621-4933-b208-0df4578b4983',
                '80e13f4a-6621-4933-b208-0df4578b4983'
            ),
            (
                '2c06d799-a80a-4806-9c2b-70d908249edd',
                '2c06d799-a80a-4806-9c2b-70d908249edd'
            )
        ], indirect=['dummy_context']
    )
    def test_expected(self, dummy_context, request_id):
        dummy_handler(None, dummy_context)
        assert os.environ['LAMBDA_REQUEST_ID'] == request_id
