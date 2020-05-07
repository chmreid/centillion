import typing
import datetime

from centillion.doctypes.doctype import Doctype


######################
# Test Doctype classes
######################


class PlainDoctype(Doctype):
    """
    This class is a plain doctype that uses the common schema.

    Unlike other doctypes, there is no single source of truth when
    creating a list of all plain documents. Therefore this class
    contains a document registry, and each document that should be
    present in the remote_list must be registered first.

    See the register_document() method.
    """
    doctype = "plain"
    name: typing.Optional[str] = None
    schema: typing.Dict[str, typing.Any] = {}

    # Define a registry of documents to return in remote_list
    document_registry: typing.List[typing.Any] = []

    def __init__(self, *args, **kwargs):
        self.name = args[0]

    @classmethod
    def register_document(cls, doc):
        if doc not in cls.document_registry:
            cls.document_registry.append(doc)

    def validate_credentials(self):
        pass

    @classmethod
    def get_remote_map(cls) -> typing.Dict[str, datetime.datetime]:
        remote_map: typing.Dict[str, datetime.datetime] = {}
        for doc in cls.document_registry:
            remote_map[doc['id']] = doc['modified_time']
        return remote_map

    @classmethod
    def get_by_id(cls, doc_id):
        for doc in cls.document_registry:
            if doc['id'] == doc_id:
                return doc

    def render_search_results(cls, whoosh_search_result):
        pass
