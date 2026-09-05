# app/tools/base.py
import time
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def call_with_retry(func, *args, **kwargs):
    """
    Calls any function with retry logic and exponential backoff.
    Retries on transient errors (timeouts, 5xx, rate limits).
    Fails immediately on permanent errors (bad request, auth failure).
    """
    max_retries = settings.max_retries
    backoff = settings.retry_backoff_seconds
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt} of {max_retries}")
            result = func(*args, **kwargs)
            return result

        except PermanentError as e:
            # No point retrying — bad request or auth failure
            logger.error(f"Permanent error, not retrying: {e}")
            raise

        except Exception as e:
            last_error = e
            wait_time = backoff * (2 ** (attempt - 1))  # 2s, 4s, 8s
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    logger.error(f"All {max_retries} attempts failed.")
    raise RetryExhaustedError(f"All retries exhausted. Last error: {last_error}")


class PermanentError(Exception):
    """
    Raised when the error is not retryable.
    Examples: invalid API key, malformed request (4xx errors except 429)
    """
    pass


class RetryExhaustedError(Exception):
    """
    Raised when all retry attempts have been exhausted.
    The DAG will catch this and route to the fallback node.
    """
    pass