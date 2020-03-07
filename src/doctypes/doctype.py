import logging
from whoosh import fields, index


class Doctype(metaclass=DoctypeRegistry):
    """
    Doctype is the base doctype class.

    User specifies credentials in config file, and links to a doctype class.

    Each doctype class should define:
    - constructor: takes credentials as input, validate credentials
    - validate credentials: does what it says
    - doc iterator: return an Iterator class
    - schema (static method): return the whoosh schema of this doctype
    - sync: use doc iterator and search to add/update/delete documents
    - search result template (static method): render a search result of this doctype
    """
    common_schema = dict(
        id = fields.ID(stored=True, unique=True),
        fingerprint = fields.ID(stored=True),
        kind = fields.ID(stored=True),
        created_time = fields.DATETIME(stored=True),
        modified_time = fields.DATETIME(stored=True),
        indexed_time = fields.DATETIME(stored=True),
        name = fields.TEXT(stored=True, field_boost=100.0)
    )
    schema = dict()

    def __init__(self, *args, *kwargs):
        raise NotImplementedError()

    def _not_implemented(self, meth):
        msg = f"Error: {meth}() not implemented for document type {self.__class__.__name}"
        raise NotImplementedError(msg)

    def validate_credentials(self):
        self._not_implemented('validate_credentials')

    def get_doc_iterator(self):
        self._not_implemented('get_doc_iterator')

    @classmethod
    def get_common_schema(cls):
        """Return a copy of the common schema shared by all document types"""
        return cls.common_schema.copy()

    @classmethod
    def get_schema(cls):
        """Return a copy of this doctype's custom, non-common schema fields"""
        return cls.schema.copy()

    def sync(self):
        self._not_implemented('sync')

    @classmethod
    def search_result_template(cls):
        self._not_implemented('search_result_template')
