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
        _schema.update(Doctype.common_schema)

        # Get the doctype schemas
        doctypes_list = Config.get_doctypes()
        for doctype in doctypes_list:
            this_doctype_cls = Doctype.REGISTRY[doctype]
            this_doctype_schema = this_doctype_cls.schema
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

    def sync_documents(
        self,
        credentials_list: typing.Optional[typing.List[str]] = None,
        doctypes_list: typing.Optional[typing.List[str]] = None
    ):
        """
        Synchronize documents (of the specified doctypes) between the remote and the local search index.
        If no doctypes are specified, performs sync for all doctypes.

        :param list doctype_list: (optional) list of doctypes to synchronize; if none specified, syncs all doctypes
        """
        doctypes_names_map = Config.get_doctypes_names_map()

        # Iterate over each doctype
        if doctypes_list is None:
            doctypes_list = Config.get_doctypes()

        for doctype in doctypes_list:

            if credentials_list is None:
                credentials_names = doctypes_names_map[doctype]

            # Within each doctype, iterate over each set of credentials
            for cred_name in credentials_names:
                doctype_instance = Doctype.REGISTRY[doctype](cred_name)

                # Get remote map
                remote_map = doctype_instance.get_remote_map()
                remote_items = set(remote_map.keys())

                # Get local map
                local_map = self.get_local_map(doctype)
                local_items = set(local_map.keys())

                # Some set math
                to_add = remote_items - local_items
                to_delete = local_items - remote_items
                to_update = remote_items.intersection(local_items)

                # Carry out orders
                self.add_docs(to_add, doctype_instance)
                self.delete_docs(to_delete)
                self.update_docs(to_update, remote_map, doctype_instance)

    def get_by_id(self, doc_id):
        """
        Get a particular document using its id
        """
        with self.ix.searcher() as s:
            kw = {SCHEMA_LABELS_ID: doc_id}
            for doc in s.documents(**kw):
                return doc

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

    def add_docs(
        self,
        to_add: typing.Union[typing.List[str], typing.Set[str]],
        doctype_instance
    ) -> None:
        """
        Automatically add documents whose IDs are in the set to_add
        to the search index. Automatically uses get_by_id in Doctype class.

        :param set to_add: set of document IDs to add to the index
        :param doctype_instance: reference to the doctype class for these documents
        """
        writer = self.ix.writer()
        for a in to_add:
            doc = doctype_instance.get_by_id(a)
            writer.add_document(**doc)
        writer.commit()

    def add_doc(self, doc: typing.Dict[str, typing.Any]) -> None:
        """Manually add a single JSON document to the search index"""
        writer = self.ix.writer()
        writer.add_document(**doc)
        writer.commit()

    def delete_docs(
        self,
        to_delete: typing.Union[typing.List[str], typing.Set[str]],
    ) -> None:
        """
        Delete all documents in a set of document IDs from the local index. Called once per doctype.

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
        to_update: typing.Union[typing.List[str], typing.Set[str]],
        doctype_instance,
        remote_map: typing.Optional[typing.Dict[str, datetime.datetime]] = None,
    ) -> None:
        """
        Given a list of document IDs that exist both at the remote and in the local index,
        determine which documents to update, and update them.

        The remote_map parameter can optionally be passed in, if it requires time/API calls to assemble.
        If it is left out, we use the doctype_instance to get a fresh remote map.

        :param set to_update: set of document IDs that exist in index and in remote
        :param doctype_instance: instance of the Doctype class for the documents being updated
        :param dict remote_map: (optional) map of remote document IDs to remote date modified
        """
        writer = self.ix.writer()
        if remote_map is None:
            remote_map = doctype_instance.get_remote_map()
        local_map = self.get_local_map(doctype_instance.doctype)
        for doc_id in to_update:
            remote_modified = remote_map[doc_id]
            local_modified = local_map[doc_id]
            # Compare dates, update doc in search index with remote if remote is newer
            if remote_modified > local_modified:
                doc = doctype_instance.get_by_id(doc_id)
                writer.update_document(**doc)
        writer.commit()

    def search(self):
        # TODO
        pass
