import logging
import functools
import os
import time
import unittest
from functools import wraps

from centillion.config import Config

from . import STANDALONE_CONFIG_PATH, INTEGRATION_CONFIG_PATH


logger = logging.getLogger(__name__)


#################
# Test decorators
#################


def eventually(timeout: float, interval: float, errors: set = {AssertionError}):
    """
    @eventually runs a test until all assertions are satisfied or a timeout is reached.
    :param timeout: time until the test fails
    :param interval: time between attempts of the test
    :param errors: the exceptions to catch and retry on
    :return: the result of the function or a raised assertion error
    """

    def decorate(func):
        @functools.wraps(func)
        def call(*args, **kwargs):
            timeout_time = time.time() + timeout
            error_tuple = tuple(errors)
            while True:
                try:
                    return func(*args, **kwargs)
                except error_tuple as e:
                    if time.time() >= timeout_time:
                        raise
                    logger.debug("Error in %s: %s. Retrying after %s s...", func, e, interval)
                    time.sleep(interval)

        return call

    return decorate


def skip_on_travis(test_item):
    """Decorator to skip tests on Travis"""
    if os.environ.get("TRAVIS") == "true":
        return unittest.skip("Test doesn't run on travis.")(test_item)
    else:
        return test_item


def standalone_test(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if is_standalone():
            Config(STANDALONE_CONFIG_PATH)
        unittest.skipUnless(is_standalone(), "Skipping standalone test")(f)(self)
        Config.reset()
    return wrapper


def is_standalone():
    return _test_mode() == "standalone"


def integration_test(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if is_integration():
            Config(INTEGRATION_CONFIG_PATH)
        unittest.skipUnless(is_integration(), "Skipping integration test")(f)(self)
        Config.reset()
    return wrapper


def is_integration():
    return _test_mode() == "integration"


def always(f):
    if is_standalone():
        Config(STANDALONE_CONFIG_PATH)
    if is_integration():
        Config(INTEGRATION_CONFIG_PATH)
        return f


def _test_mode():
    # If this environment variable is unset, it will be set to "standalone"
    return os.environ.get("CENTILLION_TEST_MODE", "standalone")
