from centillion.doctypes import DoctypeRegistry


class Search(object):
    """
    centillion Search class defines basic, high-level operations:
    - constructor
    - schema
    - open (create/open) index
    - sync (add/update/delete) documents
    - test add/update documents
    - search

    Most of the detail is handled by low-level,
    registered subclasses handling different
    document types.
    """
    def __init__(self):
        pass

    def get_schema(self):
        schema = self._get_global_schema()
        for doctype in DoctypeRegistry.get_registry():
            schema.update(doctype.get_schema())
        self._validate_schema(schema)
        return schema

    def _validate_schema(self):
        pass

    def open_index(self):
        pass

    def _create_new_index(self):
        pass

    def _open_existing_index(self):
        pass

    def sync_documents(self):
        pass

    def test_sync_documents(self):
        pass

    def search(self):
        pass
