import os
import logging

from .context import TempCentillionConfig
from .util_configs import (
    get_plain_config,
    get_invalid_ghfile_config,
)
from .util_searchdocs import (
    get_plain_doc,
    get_ghfile_doc,
)


logger = logging.getLogger(__name__)


test_dir = os.path.abspath(os.path.dirname(__file__))
repo_root = os.path.join(test_dir, "..")
config_dir = os.path.join(repo_root, "config")

STANDALONE_CONFIG_PATH = os.path.join(config_dir, "config.example.json")
INTEGRATION_CONFIG_PATH = os.path.join(config_dir, "config.integration.json")
