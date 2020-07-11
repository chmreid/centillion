import unittest
import logging

from centillion.doctypes.registry import DoctypeRegistry
from centillion.doctypes.doctype import Doctype


logger = logging.getLogger(__name__)

DOCTYPES = ["subclass_a", "subclass_b", "subclass_c"]


class DoctypeRegistryTest(unittest.TestCase):
    """
    Check the DoctypeRegistry metaclass works as intended
    """

    class _TestDoctypeSubclassA(metaclass=DoctypeRegistry):
        doctype = DOCTYPES[0]

    class _TestDoctypeSubclassB(metaclass=DoctypeRegistry):
        doctype = DOCTYPES[1]

    class _TestDoctypeSubclassC(metaclass=DoctypeRegistry):
        doctype = DOCTYPES[2]

    class _TestDoctypeSubclassD(metaclass=DoctypeRegistry):
        pass

    def test_registry(self):
        for doctype in DOCTYPES:
            self.assertIn(doctype, DoctypeRegistry.get_registry())

    def test_registry_noattr(self):
        self.assertIn(self._TestDoctypeSubclassD.__name__, DoctypeRegistry.get_registry())


class DoctypeTest(unittest.TestCase):
    """
    Check the Doctype base class works as intended
    """

    def test_constructor(self):
        """
        Test the base doctype cannot be used
        """
        with self.assertRaises(NotImplementedError):
            Doctype()

    def test_schema(self):
        """
        Test the schema is configured properly and is accessible
        """
        # Ensure common schema is set
        required_keys = [
            "id",
            "fingerprint",
            "kind",
            "created_time",
            "modified_time",
            "indexed_time",
            "name",
        ]
        schema_keys = list(Doctype.common_schema.keys())
        for req_key in required_keys:
            self.assertIn(req_key, schema_keys)
        # Ensure base schema is empty
        self.assertDictEqual(Doctype.schema, {})

    def test_doctype(self):
        """Test the doctype class var is configured and accessible"""
        self.assertEqual(Doctype.doctype, "base")


if __name__ == "__main__":
    unittest.main()
