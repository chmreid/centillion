"""Defines doctype functionality"""
import logging
import typing
from whoosh import fields

from .registry import DoctypeRegistry


logger = logging.getLogger(__name__)

SCHEMA_LABELS_ID = "id"
SCHEMA_LABELS_DOCTYPE = "kind"
SCHEMA_LABELS_MODIFIED = "modified_time"


class Doctype(metaclass=DoctypeRegistry):
    doctype = "base"
    """
    Doctype is the base doctype class.

    User specifies credentials in config file, and links to a doctype class.

    Each doctype class should define:
    - constructor: takes credentials as input, validate credentials
    - validate credentials: does what it says
    - schema (class attribute)
    - get_remote_map: list of remote document IDs and last modified date
    - get_by_id: get document by index ID, return item matching common + doctype schema
    - search result template (static method): render a search result of this doctype
    """
    common_schema = dict(
        id=fields.ID(stored=True, unique=True),
        fingerprint=fields.ID(stored=True),
        kind=fields.ID(stored=True),
        created_time=fields.DATETIME(stored=True),
        modified_time=fields.DATETIME(stored=True),
        indexed_time=fields.DATETIME(stored=True),
        name=fields.TEXT(stored=True, field_boost=100.0),
    )
    schema: typing.Dict[str, typing.Any] = dict()

    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def _not_implemented(cls, meth):
        msg = f"Error: {meth}() not implemented for document type {cls.__name__}"
        raise NotImplementedError(msg)

    def validate_credentials(self):
        self._not_implemented("validate_credentials")

    def get_remote_map(self):
        self._not_implemented("get_remote_map")

    def get_by_id(self, doc_id):
        self._not_implemented("get_by_id")

    @classmethod
    def render_search_result(cls, whoosh_search_result):
        cls._not_implemented("render_search_result")

    @classmethod
    def get_jinja_template(cls):
        cls._not_implemented("get_jinja_template")

    @classmethod
    def get_doctype(cls):
        """Return the string label for this doctype"""
        logger.debug("Fetching class doctype")
        return cls.doctype
