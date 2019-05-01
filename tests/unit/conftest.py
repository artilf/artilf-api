import os

import pytest

os.environ['Env'] = 'development'


class DummyContext(object):
    def __init__(self, request_id):
        self.aws_request_id = request_id


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
