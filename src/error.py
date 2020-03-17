import json
import werkzeug.exceptions
import functools
import traceback
import requests
import logging
from flask import Response as FlaskResponse


logger = logging.getLogger(__name__)


class CentillionException(Exception):
    """A base class for raising Flask-friendly exceptions from centillion"""

    def __init__(self, status: int, code: str, title: str, *args, **kwargs) -> None:
        super().__init__(title)  # type: ignore
        self.status = status
        self.code = code
        self.message = title


class CentillionConfigException(CentillionException):
    """
    Configuration exception class, raised by Config class.
    """

    def __init__(self, title: str = "Error: the centillion configuration file has a problem", *args, **kwargs) -> None:
        super().__init__(
            requests.codes.internal_server_error, "Configuration Error", title, *args, **kwargs
        )


class CentillionForbiddenException(CentillionException):
    """
    Forbidden exception class, raised by Flask auth layer.
    """

    def __init__(self, title: str = "User not authorized", *args, **kwargs) -> None:
        super().__init__(requests.codes.forbidden, "Forbidden", title, *args, **kwargs)


def centillion_exception_handler(e: CentillionException) -> FlaskResponse:
    """
    Turn Centillion exceptions into Flask exceptions.
    This is added to the Flask app as an error handler.

    Example:

        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> app.register_error_handler(CentillionException, centillion_exception_handler)
    """
    return FlaskResponse(
        status=e.status,
        mimetype="application/problem+json",
        content_type="application/problem+json",
        response=json.dumps(
            {
                "status": e.status,
                "code": e.code,
                "title": e.message,
                "stacktrace": traceback.format_exc(),
            }
        ),
    )


def centillion_handler(func):
    """
    Generally, each route handler should be decorated with @centillion_handler, which manages exceptions.
    Handlers that are not decorated are returned to app.common_error_handler(Exception).
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except werkzeug.exceptions.HTTPException as ex:
            status = ex.code
            code = ex.name
            title = str(ex)
            stacktrace = traceback.format_exc()
        except CentillionException as ex:
            status = ex.status
            code = ex.code
            title = ex.message
            stacktrace = traceback.format_exc()
        except Exception as ex:
            status = requests.codes.server_error
            code = "unhandled_exception"
            title = str(ex)
            stacktrace = traceback.format_exc()
        logger.error(
            json.dumps(dict(status=status, code=code, title=title, stacktrace=stacktrace), indent=4)
        )
