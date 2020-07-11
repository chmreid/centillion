import typing


"""
Utility Functions for Configurations
"""


def get_empty_config() -> typing.Dict[str, typing.Any]:
    """
    Create a simple configuration file that tests can use.
    - We don't set centillion root because the TempCentillionConfig
      context manager will do that for us
    - We don't set centillion indexdir because by default it is at
      $centillion_root/index
    - doctype is empty
    """
    return {
        "doctypes": [],
    }


def get_plain_config() -> typing.Dict[str, typing.Any]:
    """
    Create a config file with a plain type document (defined for tests only)
    """
    return {
        "doctypes": [{
            "name": "centillion-test-search-plain",
            "doctype": "plain"
        }]
    }


def get_invalid_ghfile_config():
    """
    Create a Github file configuration file that tests can use.
    """
    return {
        "doctypes": [{
            "name": "centillion-test-search-invalid-ghfile",
            "doctype": "github_file",
            "access_token": "invalid-access-token",
            "repos": [
                "charlesreid1/centillion-search-demo"
            ]
        }]
    }
