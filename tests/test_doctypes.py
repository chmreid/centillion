import unittest
import logging

from centillion.doctypes.registry import DoctypeRegistry
from centillion.doctypes.doctype import Doctype


logger = logging.getLogger(__name__)

DOCTYPES = ["subclass_a", "subclass_b", "subclass_c"]  # subclass_d is intentionally excluded

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
        """Test that the new doctypes are in the Doctype registry, using the doctype attribute"""
        for doctype in DOCTYPES:
            self.assertIn(doctype, DoctypeRegistry.get_registry())

    def test_registry_noattr(self):
        """Test that the new doctypes are in the Doctype registry, even if no doctype attribute is defined"""
        self.assertIn(self._TestDoctypeSubclassD.__name__, DoctypeRegistry.get_registry())

    def test_registry(self):
        """
        Check that the doctype registry returns instances of the correct class
        """
        self.assertEqual(type(cls.get_registry()["subclass_a"]), self._TestDoctypeSubclassA)
        self.assertEqual(type(cls.get_registry()["subclass_b"]), self._TestDoctypeSubclassB)
        self.assertEqual(type(cls.get_registry()["subclass_c"]), self._TestDoctypeSubclassC)
        self.assertEqual(type(cls.get_registry()[self._TestDoctypeSubclassD.__name__]), self._TestDoctypeSubclassD)


class DoctypeVirtualMethodsTest(unittest.TestCase):
    """
    Check that if a derived doctype class does not have virtual methods defined,
    centillion will raise a NotImplementedError.
    """
    class _TestDoctypeVirtualMethodsSubclassA(metaclass=DoctypeRegistry):
        def __init__(self, *args, **kwargs):
            pass

    def test_virtual_method_init(self):
        """
        Check that a Doctype method that defines a constructor but no virtual methods will cause exceptions.
        """
        instanceA = self._TestDoctypeVirtualMethodsSubclassA()
        with self.assertRaises(NotImplementedError):
            instanceA.validate_credentials()
        with self.assertRaises(NotImplementedError):
            instanceA.get_remote_map()
        with self.assertRaises(NotImplementedError):
            instanceA.get_by_id()
        with self.assertRaises(NotImplementedError):
            instanceA.get_jinja_template()


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
