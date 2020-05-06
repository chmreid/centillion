import logging
import typing
import datetime
from functools import lru_cache
from whoosh import index
# from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.fields import Schema

from ..doctypes.doctype import (
    Doctype,
    SCHEMA_LABELS_ID,
    SCHEMA_LABELS_DOCTYPE,
    SCHEMA_LABELS_MODIFIED,
)
from ..config import Config
from ..error import CentillionSearchIndexException


logger = logging.getLogger(__name__)


class Search(object):
    """
    centillion Search class defines basic, high-level operations:
    - constructor
    - schema
    - open (create/open) index
    - sync (add/update/delete) documents
    - search

    Most of the detail is handled by low-level,
    registered subclasses handling different
    document types.
    """
    def __init__(self):
        # Initialize the schema
        self.get_schema()
        self.open_index()

    @lru_cache(maxsize=32)
    def get_schema(self):
        # This dictionary will be converted to a Schema object
        _schema = {}

        # Get the common schema
        common_schema = Doctype.get_common_schema()
        _schema.update(common_schema)

        # Get the doctype schemas
        doctypes_list = Config.get_doctypes()
        for doctype in doctypes_list:
            this_doctype_cls = Doctype.REGISTRY[doctype]
            this_doctype_schema = this_doctype_cls.get_schema()
            # For each schema field, check it does not conflict with our schema, then add it
            for schema_field in this_doctype_schema:
                if schema_field in _schema:
                    # Field is already in schema, check that types match
                    type_theirs = type(this_doctype_schema[schema_field])
                    type_ours = type(_schema[schema_field])
                    if type_theirs != type_ours:
                        err = "Error: schema mismatch with existing index for field "
                        err += f"{schema_field}, doctype {doctype}"
                        raise CentillionSearchIndexException(err)
                else:
                    # Field is not in schema, add it to the schema
                    _schema[schema_field] = this_doctype_schema[schema_field]

        self.schema = Schema(**_schema)
        return self.schema

    def open_index(self):
        """Open an index, creating it if necessary"""
        indexdir = Config.get_centillion_indexdir()

        # Create or open index
        if index.exists_in(indexdir):
            self._open_index()
        else:
            self._create_index()

    def _open_index(self):
        """Open an existing index"""
        indexdir = Config.get_centillion_indexdir()
        self.ix = index.open_dir(indexdir)
        if self.schema != self.ix.schema:
            err = f"Error: schema mismatch! Specified schema from config file does not "
            err += f"match schema of existing search index."
            raise CentillionSearchIndexException(err)

    def _create_index(self):
        """Create a new index"""
        indexdir = Config.get_centillion_indexdir()
        self.ix = index.create_in(indexdir, self.schema)

    def sync_documents(self, doctypes_list: typing.Optional[typing.List[str]] = None):
        """
        Synchronize documents (of the specified doctypes) between the remote and the local search index.
        If no doctypes are specified, performs sync for all doctypes.

        :param list doctype_list: (optional) list of doctypes to synchronize; if none specified, syncs all doctypes
        """
        if doctypes_list is None:
            doctypes_list = Config.get_doctypes()

        # For each doctype, perform sync operation
        for doctype in doctypes_list:
            doctype_cls = Doctype.REGISTRY[doctype]

            # Get remote map
            remote_map = doctype_cls.get_remote_map()
            remote_items = set(remote_map.keys())

            # Get local map
            local_map = self.get_local_map(doctype)
            local_items = set(local_map.keys())

            # Some set math
            to_add = remote_items - local_items
            to_delete = local_items - remote_items
            to_update = remote_items.intersection(local_items)

            self.add_docs(to_add, doctype_cls)
            self.delete_docs(to_delete)
            self.update_docs(to_update, remote_map, local_map, doctype_cls)

    def get_local_map(self, doctype: str) -> typing.Dict[str, datetime.datetime]:
        """
        Compile a map of document IDs (in the index) to last modified date.
        This is used to determine which documents in index need updating.

        :returns: map of doc_id (str) to last_modified_date (datetime)
        """
        local_map = {}
        with self.ix.searcher() as s:
            kw = {SCHEMA_LABELS_DOCTYPE: doctype}
            for doc in s.documents(**kw):
                doc_id = doc[SCHEMA_LABELS_ID]
                doc_date = doc[SCHEMA_LABELS_MODIFIED]
                local_map[doc_id] = doc_date
        return local_map

    def add_docs(self, to_add: typing.Set[str], doctype_cls) -> None:
        """
        Add all documents in a list of document IDs. Called once per doctype.

        :param set to_add: set of document IDs to add to the index
        :param doctype_cls: reference to the doctype class for these documents
        """
        writer = self.ix.writer()
        for a in to_add:
            doc = doctype_cls.get_by_id(a)
            writer.add_document(**doc)
        writer.commit()

    def add_doc(self, doc: typing.Dict[str, typing.Any]) -> None:
        """Add a single document to the search index"""
        writer = self.ix.writer()
        writer.add_document(**doc)
        writer.commit()

    def delete_docs(self, to_delete) -> None:
        """
        Delete all documents in a list of document IDs from the local index. Called once per doctype.

        :param set to_delete: set of document IDs to delete
        """
        writer = self.ix.writer()
        for doc_id in to_delete:
            writer.delete_by_term(SCHEMA_LABELS_ID, doc_id)
        writer.commit()

    def delete_doc(self, doc_id: str) -> None:
        """Delete a single document from the search index"""
        writer = self.ix.writer()
        writer.delete_by_term(SCHEMA_LABELS_ID, doc_id)
        writer.commit()

    def update_docs(
        self,
        to_update: typing.Set[str],
        remote_map: typing.Dict[str, datetime.datetime],
        local_map: typing.Dict[str, datetime.datetime],
        doctype_cls
    ) -> None:
        """
        Given a list of document IDs that exist both at the remote and in the local index,
        determine which documents to update, and update them.

        :param set to_update: set of document IDs that exist in index and in remote
        :param dict remote_map: map of remote document IDs to remote date modified
        :param dict local_map: map of local index document IDs to local index date modified
        :param doctype_cls: reference to Doctype class for this document
        """
        writer = self.ix.writer()
        for doc_id in to_update:
            remote_modified = remote_map[doc_id]
            local_modified = local_map[doc_id]
            # Compare dates
            # If remote modified is more recent, update doc
            if remote_modified > local_modified:
                doc = doctype_cls.get_by_id(doc_id)
                writer.update_document(doc)
        writer.commit()

    def search(self):
        # TODO
        pass
