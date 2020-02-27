from whoosh import fields, index


class Doctype(metaclass=DoctypeRegistry):
    """
    Doctype is the base doctype class.
    Any subclass of Doctype will register itself
    in the Doctype Registry and will implement
    methods to:
    - auth
    - schema
    - way to iterate over all documents
    - way to do add/update/delete (sync)
    - way to render search results to html
    """
    def _not_implemented(self, meth):
        msg = f"Error: {meth}() not implemented for document type {self.__class__.__name}"
        raise NotImplementedError(msg)

    def auth(self):
        """
        Do the security flow, fails if exceptions raised
        """
        self._not_implemented('auth')

    def sync(self):
        """
        Add/update/delete all documents.
        """
        self._not_implemented('sync')

    def schema(self):
        """
        Return the schema in the form of a dictionary,
        field names are keys and whoosh types are values.

        Global schema is implemented as a private method,
        so each component can assimilate the global schema
        into their own without any of that super() business.
        """
        self._not_implemented('schema')

    def _get_global_schema(self):
        """
        Return dict containing the global centillion schema.
        This still needs to be augmented and passed to
        the Schema() constructor.

        Global schema for all documents in centillion:
        - id
        - fingerprint
        - kind
        - created time
        - modified time
        - indexed time
        - name (title?)
        """
        return {
            id = fields.ID(stored=True, unique=True),
            fingerprint = fields.ID(stored=True),
            kind = fields.ID(stored=True),
            created_time = fields.DATETIME(stored=True),
            modified_time = fields.DATETIME(stored=True),
            indexed_time = fields.DATETIME(stored=True),
            name = fields.TEXT(stored=True, field_boost=100.0)
        }
