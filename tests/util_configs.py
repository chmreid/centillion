"""
Utility Functions for Configurations
"""


def get_plain_config() -> typing.Dict[str, typing.Any]:
    """
    Create a simple configuration file that tests can use.
    - We don't set centillion root because the TempCentillionConfig
      context manager will do that for us
    - We don't set centillion indexdir because by default it is at
      $centillion_root/index
    """
    return {
        "doctypes": [],
    }


def get_invalid_ghfile_config():
    """
    Create a Github file configuration file that tests can use.
    """
    return {
        "doctypes": [{
            "name": "centillion-test-search-get-local-map",
            "doctype": "github_file",
            "access_token": "invalid-access-token",
            "repos": [
                "charlesreid1/centillion-search-demo"
            ]
        }]
    }
