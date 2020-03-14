import logging
import functools
import os
import time
import unittest

from centillion import Config


logger = logging.getLogger(__name__)

test_dir = os.path.abspath(os.path.dirname(__file__))
config_dir = os.path.join(os.path.dirname(__file__), "..", "config")  # noqa

STANDALONE_CONFIG_PATH = os.path.join(config_dir, "config.example.json")
INTEGRATION_CONFIG_PATH = os.path.join(test_dir, "config.integration.json")


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
    if is_standalone():
        Config(STANDALONE_CONFIG_PATH)
    return unittest.skipUnless(is_standalone(), "Skipping standalone test")(f)


def is_standalone():
    return "standalone" in _test_mode()


def integration_test(f):
    if is_integration():
        Config(INTEGRATION_CONFIG_PATH)
    return unittest.skipUnless(is_integration(), "Skipping integration test")(f)


def is_integration():
    return "integration" in _test_mode()


def always(f):
    return f


def _test_mode():
    # TODO: document this env var. if unset, run standalone unit tests
    return os.environ.get("CENTILLION_TEST_MODE", "standalone")
