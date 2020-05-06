import os
import logging

# These imports register the test doctypes in the doctype registry
from .doctypes import plain  # noqa


logger = logging.getLogger(__name__)


test_dir = os.path.abspath(os.path.dirname(__file__))
repo_root = os.path.join(test_dir, "..")
config_dir = os.path.join(repo_root, "config")

STANDALONE_CONFIG_PATH = os.path.join(config_dir, "config.example.json")
INTEGRATION_CONFIG_PATH = os.path.join(config_dir, "config.integration.json")
