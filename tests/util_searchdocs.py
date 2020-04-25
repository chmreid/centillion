import typing
import datetime

"""
Utility Functions for Search Documents
"""


def get_plain_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """Return a document that only sets fields in the common schema"""
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo",
        kind = "foobar",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        indexed_time = datetime.datetime.now(),
        name = f"file_{ix}.dat",
    )


def get_ghfile_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """Return a document that only sets fields in the Github file schema"""
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo",
        kind = "github_file",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        indexed_time = datetime.datetime.now(),
        name = f"file_{ix}.dat",
        file_name = f"file_{ix}.dat",
        file_url = f"https://github.com/charlesreid1/centillion-search-demo/tree/master/file_{ix}.dat",
        repo_path = f"file_{ix}.dat",
        github_user = "charlesreid1",
    )


def get_ghpr_doc(ix: int) -> typing.Dict[str, typing.Any]:
    title = "Hello World This Is A Pull Request"
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo/issues/1",
        kind = "github_issue_pr",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        indexed_time = datetime.datetime.now(),
        name = title,
        issue_title = title,
        issue_url = "",
        repo_name = "charlesreid1/centillion-search-demo",
        github_user = "charlesreid1",
        content = "Hello world! This is some content."
    )


def get_ghissue_doc(ix: int) -> typing.Dict[str, typing.Any]:
    title = "Hello World This Is An Issue"
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo/issues/1",
        kind = "github_issue_pr",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        indexed_time = datetime.datetime.now(),
        name = title,
        issue_title = title,
        issue_url = "",
        repo_name = "charlesreid1/centillion-search-demo",
        github_user = "charlesreid1",
        content = "Hello world! This is some content."
    )
