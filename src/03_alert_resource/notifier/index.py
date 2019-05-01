from logger.aws_lambda_tools import save_request_id
from logger.get_logger import get_logger
from notifier import main

logger = get_logger(__name__)


@save_request_id
def handler(event, context):
    try:
        main(event)
    except Exception as e:
        logger.error(f'Exception occurred: {e}', exc_info=True)
        raise
