import os
import shutil
import typing
import itertools
import unittest
import datetime

from . import temp_dir as centillion_temp_dir
from .decorators import is_integration

from centillion.doctypes.doctype import Doctype


class DoctypeTestMixin(unittest.TestCase):
    """
    Adds a check for given doctypes in a given config file.

    This class provides one main method, _iterate_doctypes.
    This method constructs an instance of each doctype class,
    and calls an action on it.
    """

    def _iterate_doctypes(
        self,
        doctypes_to_check: typing.List[str],
        doctypes_names_map: typing.Dict[str, typing.List[str]],
        action
    ):
        """
        Given a list of doctypes to check, and a map of doctypes to credential names,
        use the doctype registry to get a reference to each doctype class.
        Requires real (integration) credentials.
        Calls _action() for each doctype instance.

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        :param action: function to perform on each doctype instance after constructing it
        """
        for doctype in doctypes_to_check:
            self.assertIn(doctype, doctypes_names_map)
            names = doctypes_names_map[doctype]
            name = names[0]
            with self.subTest(f"Check doctype constructor for {doctype} using credentials {name}"):

                # Doctype gives name, name is passed to constructor.
                # Doctype gives class ref via registry.
                registry = Doctype.get_registry()
                DoctypeCls = registry[doctype]

                # Make the doctype class (also performs credentials validation).
                doctype = DoctypeCls(name)
                action(doctype)


class ConstructorTestMixin(DoctypeTestMixin):
    """
    Adds a check for constructors of a given doctype in a given config file.
    """

    def check_doctype_constructors(self, *args, **kwargs):
        """
        Iterate over each doctype in doctypes_to_check, assemble an instance of each class.
        Then call action on each one (to test constructor, do nothing).

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        """
        def _action(doctype):
            """Let _iterate_doctypes() do all the work of calling constructors"""
            pass

        # Calls _action() on each doctype class
        self._iterate_doctypes(*args, **kwargs, action=_action)


class RemoteListTestMixin(DoctypeTestMixin):
    """
    Adds a check for the remote_list function of a given doctype in a given config file.
    """

    def check_doctype_remote_map(self, *args, **kwargs):
        """
        Given a map of doctypes to credential names, get the type of each name
        and call the constructor of that class. Requires real credentials.

        :param doctypes_to_check: list of strings of doctypes to check
        :param doctypes_names_map: map of doctypes to list of names of credentials matching that doctype
        """
        def _action(doctype):
            remote_map = doctype.get_remote_map()
            # Verify remote map is a map of strings to dates
            for name, date in remote_map.items():
                self.assertEqual(type(name), str)
                self.assertEqual(type(date), datetime.datetime)

        self._iterate_doctypes(*args, **kwargs, action=_action)


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


class IntegrationTestMixin(unittest.TestCase):
    """
    Adds a setUp and tearDown method for this unit test class
    that will ensure /tmp/centillion is available during the test
    and is deleted after the test is finished.
    """
    @classmethod
    def setUp(self):
        if is_integration():
            if not os.path.exists(centillion_temp_dir):
                os.makedirs(centillion_temp_dir)

    @classmethod
    def tearDown(self):
        if is_integration():
            if os.path.exists(centillion_temp_dir):
                shutil.rmtree(centillion_temp_dir)
            else:
                raise Exception(f"Error: temporary directory {centillion_temp_dir} disappeared during a test")
