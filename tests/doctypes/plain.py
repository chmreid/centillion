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
    # Keys are document IDs, values are documents
    document_registry: typing.Dict[str, typing.Any] = {}

    def __init__(self, *args, **kwargs):
        self.name = args[0]

    @classmethod
    def register_document(cls, doc):
        cls.document_registry[doc['id']] = doc

    def validate_credentials(self):
        pass

    @classmethod
    def get_remote_map(cls) -> typing.Dict[str, datetime.datetime]:
        remote_map: typing.Dict[str, datetime.datetime] = {}
        for doc_id, doc in cls.document_registry.items():
            remote_map[doc_id] = doc['modified_time']
        return remote_map

    @classmethod
    def get_by_id(cls, doc_id):
        if doc_id in cls.document_registry.keys():
            return cls.document_registry[doc_id]
        else:
            return None

    def render_search_results(self, whoosh_search_result):
        pass


# class OldPlainDoctype(Doctype):
#     """
#     This class is a plain doctype that uses the common schema.
# 
#     Unlike other doctypes, there is no single source of truth when
#     creating a list of all plain documents. Therefore this class
#     contains a document registry, and each document that should be
#     present in the remote_list must be registered first.
# 
#     See the register_document() method.
#     """
#     doctype = "plain"
#     name: typing.Optional[str] = None
#     schema: typing.Dict[str, typing.Any] = {}
# 
#     def __init__(self, *args, **kwargs):
#         self.name = args[0]
#         # Define a registry of documents to return in remote_list
#         self.document_registry: typing.List[typing.Any] = []
# 
#     def register_document(self, doc):
#         if self.get_by_id(doc['id']) is None:
#             self.document_registry.append(doc)
#         else:
#             for registered_doc in self.document_registry:
#                 if doc['id'] == registered_doc['id']:
#                     del registered_doc
#                     self.document_registry.append(doc)
#                     break
# 
#     def validate_credentials(self):
#         pass
# 
#     def get_remote_map(self) -> typing.Dict[str, datetime.datetime]:
#         remote_map: typing.Dict[str, datetime.datetime] = {}
#         for doc in self.document_registry:
#             remote_map[doc['id']] = doc['modified_time']
#         return remote_map
# 
#     def get_by_id(self, doc_id):
#         for doc in self.document_registry:
#             if doc['id'] == doc_id:
#                 return doc
#         return None
# 
#     def render_search_results(self, whoosh_search_result):
#         pass
