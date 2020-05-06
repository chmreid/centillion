import typing

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

    See the register() method.
    """
    doctype = "plain"
    name: typing.Optional[str] = None
    schema: Doctype.common_schema

    # Define a registry of documents to return in remote_list
    document_registry = []

    def __init__(self, *args, **kwargs):
        self.name = args[0]

    def register_document(self, doc):
        if doc not in PlainDoctype.document_registry:
            PlainDoctype.document_registry.append(doc)

    def validate_credentials(self):
        pass

    def get_remote_map(self):
        pass
