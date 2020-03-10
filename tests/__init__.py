import logging
import unittest


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
    return unittest.skipUnless(is_standalone(), "Skipping standalone test")(f)


def is_standalone():
    return "standalone" in _test_mode()


def integration_test(f):
    return unittest.skipUnless(is_integration(), "Skipping integration test")(f)


def is_integration():
    return "integration" in _test_mode()


def always(f):
    return f


def _test_mode():
    # TODO: document this env var. if unset, run standalone unit tests
    return os.environ.get("CENTILLION_TEST_MODE", "standalone")


#################
# Utility classes
#################

class CaptureStdout(list):
    """
    Utility object using a context manager to capture stdout for a given block
    of Python code. Subclass of list so that you can access stdout lines like a
    list.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def __enter__(self, *args, **kwargs):
        """
        The function called when we open the context, this function swaps out
        sys.stdout with a string buffer and saves the sys.stdout reference.
        """
        # Save existing stdout object so we can restore it when we're done
        self._stdout = sys.stdout
        # Swap out stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Close the context and clean up; the *args are needed in case there is
        an exception (we don't deal with those here)
        """
        # This class extends the list class, so call self.extend to add a list
        # to the end of self. This is to add all of the new lines from the
        # StringIO object.
        self.extend(self._stringio.getvalue().splitlines())

        # Clean up (if this is missing, the garbage collector will eventually
        # take care of this...)
        del self._stringio

        # Clean up by setting sys.stdout back to what it was before we opened
        # up this context
        sys.stdout = self._stdout
