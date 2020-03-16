import typing
import itertools
import unittest
import datetime

from centillion.doctypes.doctype import Doctype

from .decorators import integration_test


class DoctypeTestMixin(unittest.TestCase):
    """
    Adds a check for given doctypes in a given config file.

    This constructs an instance of each doctype and calls _action() with it.
    """

    def _action(self, doctype):
        """Perform an action with a doctype instance"""
        raise NotImplementedError("Error: _action() not implemented for DoctypeTestMixin")

    def _iterate_doctypes(
        self,
        doctypes_to_check: typing.List[str],
        doctypes_names_map: typing.Dict[str, typing.List[str]],
    ):
        """
        Given a list of doctypes to check, and a map of doctypes to credential names,
        use the doctype registry to get a reference to each doctype class.
        Requires real (integration) credentials.
        Calls _action() for each doctype instance.

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        """
        for doctype in doctypes_to_check:
            self.assertIn(doctype, doctypes_names_map)
            name = doctypes_names_map[doctype]
            msg = f"Check doctype constructor for {doctype} using credentials {name}"
            with self.subTest(msg):

                # Doctype gives name, name is passed to constructor.
                # Doctype gives class ref via registry.
                registry = Doctype.get_registry()
                DoctypeCls = registry[doctype]

                # Make the doctype class (also performs credentials validation).
                doctype = DoctypeCls(name)
                self._action(doctype)


class ConstructorTestMixin(DoctypeTestMixin):
    """
    Adds a check for constructors of a given doctype in a given config file.
    """

    def _action(self, doctype):
        """Let _iterate_doctypes() do all the work of calling the constructors"""
        pass

    def check_doctype_constructors(self, *args, **kwargs):
        """
        Iterate over each doctype in doctypes_to_check, assemble an instance of each class.
        Then call _action() on each one (to test constructor, do nothing).

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        """
        # Calls _action() on each doctype class
        self._iterate_doctypes(*args, **kwargs)


class RemoteListTestMixin(DoctypeTestMixin):
    """
    Adds a check for the remote_list function of a given doctype in a given config file.
    """

    def _action(self, doctype):
        """Once _iterate_doctypes() calls the constructors, we call remote_list()"""
        doctype.remote_list()
        # Verify doctype list consists of (datetime, type) tuples
        for date, name in doctype.remote_list():
            self.assertEqual(type(date), datetime.datetime)
            self.assertEqual(type(name), type(""))

    def check_doctype_remote_list(self, *args, **kwargs):
        """
        Given a map of doctypes to credential names, get the type of each name
        and call the constructor of that class. Requires real credentials.

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        """
        self._iterate_doctypes(*args, **kwargs)


class SchemaTestMixin(unittest.TestCase):
    """Base class to check if schemas of related doctypes are consistent"""

    def check_consistent_schemas(self, related_doctypes):
        """If two related schemas have matching keys, they should have matching value types"""
        # Generate all pairwise combinations
        for doctype, other_doctype in itertools.combinations(related_doctypes, 2):

            msg = f"Check doctype schemas {doctype} and {other_doctype} are consistent"
            with self.subTest(msg):

                # Get class refs from doctype registry
                registry = Doctype.get_registry()
                DoctypeCls = registry[doctype]
                OtherDoctypeCls = registry[other_doctype]

                # Get schemas
                doctype_schema = DoctypeCls.schema
                other_doctype_schema = OtherDoctypeCls.schema

                # Get shared keys
                doctype_schema_keys = set(doctype_schema.keys())
                other_doctype_schema_keys = set(other_doctype_schema.keys())
                shared_schema_keys = doctype_schema_keys.intersection(other_doctype_schema_keys)

                # Verify types of shared schema keys are consistent
                for shared_key in shared_schema_keys:
                    this_type = type(doctype_schema[shared_key])
                    other_type = type(other_doctype_schema[shared_key])
                    self.assertEqual(this_type, other_type)
