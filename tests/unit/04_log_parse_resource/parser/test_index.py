import os

import pytest

import index


@pytest.mark.parametrize(
    'delete_environ', [
        (
            ['LAMBDA_REQUEST_ID']
        )
    ], indirect=True
)
@pytest.mark.usefixtures('delete_environ')
class TestHandler(object):
    @pytest.mark.parametrize(
        'raised_error, catched_error', [
            (Exception, Exception),
            (KeyError, KeyError),
            (ValueError, ValueError)
        ]
    )
    def test_exception(self, monkeypatch, raised_error, catched_error):
        def dummy_func(*args, **argv):
            raise raised_error('')
        monkeypatch.setattr(index, 'main', dummy_func)
        with pytest.raises(catched_error):
            index.handler(None, None)

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
    def test_normal(self, monkeypatch, dummy_context, request_id):
        monkeypatch.setattr(index, 'main', lambda *_: None)
        index.handler(None, dummy_context)
        assert os.environ['LAMBDA_REQUEST_ID'] == request_id
