import os
from functools import wraps

from logger.get_logger import get_logger

logger = get_logger(__name__)


def save_request_id(lambda_handler):
    @wraps(lambda_handler)
    def set_request_id_to_environ(event, context):
        try:
            os.environ['LAMBDA_REQUEST_ID'] = context.aws_request_id
        except Exception as e:
            logger.warning(f'Exception occurred: {e}', exc_info=True)
        return lambda_handler(event, context)
    return set_request_id_to_environ
