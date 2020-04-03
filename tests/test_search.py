import unittest
import tempfile
from whoosh.fields import Schema

#from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.doctype import Doctype

from .context import TempCentillionConfig


class SearchTest(unittest.TestCase):
    """
    Check the Search class works as intended
    """

    def test_constructor(self):
        """Test the creation of a Search object"""
        # Create a simple configuration file for this test.
        #
        # We don't set centillion root because the TempCentillionConfig
        # context manager will do that for us.
        #
        # We don't set centillion indexdir because by default it is at
        # $centillion_root/index.
        def get_simple_config():
            return {
                "doctypes": [],
            }

        # with TempCentillionConfig(get_simple_config()) as config_file:
        with TempCentillionConfig(get_simple_config()):
            # We did not specify any doctypes, so the schema
            # should match the common schema exactly.
            s = Search()
            search_schema = s.get_schema()
            common_schema = Schema(**Doctype.get_common_schema())
            self.assertEqual(common_schema, search_schema)
