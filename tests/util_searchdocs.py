import typing
import datetime

from centillion.doctypes.registry import DoctypeRegistry

"""
Utility Functions for Search Documents
"""


def get_plain_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """Return a document that only sets fields in the common schema"""
    return dict(
        id=f"plain-document-{ix}",
        kind="plain",
        created_time=datetime.datetime.now().replace(microsecond=0),
        modified_time=datetime.datetime.now().replace(microsecond=0),
        indexed_time=datetime.datetime.now().replace(microsecond=0),
        name=f"file_{ix}.dat",
    )


def get_plain_docs(n: int = 5) -> typing.List[typing.Dict[str, typing.Any]]:
    """Get a list of N fake plain docs"""
    name = 'centillion-test-search-util-searchdocs-get-plain-docs'
    docs: typing.List[typing.Any] = []
    doctype = "plain"
    doctype_cls = DoctypeRegistry.REGISTRY[doctype]
    doctype_instance = doctype_cls(name)
    for j in range(1, n+1):
        doc = get_plain_doc(j)
        doctype_instance.register_document(doc)
        docs.append(doc)
    return docs


def get_ghfile_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """
    Return a fake Github file (github_file doctype)
    """
    # TODO: is this supposed to be fake? or real?
    return dict(
        id="https://github.com/charlesreid1/centillion-search-demo",
        kind="github_file",
        created_time=datetime.datetime.now().replace(microsecond=0),
        modified_time=datetime.datetime.now().replace(microsecond=0),
        indexed_time=datetime.datetime.now().replace(microsecond=0),
        name=f"file_{ix}.dat",
        file_name=f"file_{ix}.dat",
        file_url=f"https://github.com/charlesreid1/centillion-search-demo/tree/master/file_{ix}.dat",
        repo_path=f"file_{ix}.dat",
        github_user="charlesreid1",
    )


def get_ghpr_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """
    Return a fake Github PR (github_issue_pr doctype)
    """
    # TODO: is this supposed to be fake? or real?
    title = "Hello World This Is A Pull Request"
    return dict(
        id="https://github.com/charlesreid1/centillion-search-demo/issues/1",
        kind="github_issue_pr",
        created_time=datetime.datetime.now().replace(microsecond=0),
        modified_time=datetime.datetime.now().replace(microsecond=0),
        indexed_time=datetime.datetime.now().replace(microsecond=0),
        name=title,
        issue_title=title,
        issue_url="",
        repo_name="charlesreid1/centillion-search-demo",
        github_user="charlesreid1",
        content="Hello world! This is some content."
    )


def get_ghissue_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """
    Return a fake Github issue (github_issue_pr doctype)
    """
    title = "Hello World This Is An Issue"
    return dict(
        id="https://github.com/charlesreid1/centillion-search-demo/issues/1",
        kind="github_issue_pr",
        created_time=datetime.datetime.now().replace(microsecond=0),
        modified_time=datetime.datetime.now().replace(microsecond=0),
        indexed_time=datetime.datetime.now().replace(microsecond=0),
        name=title,
        issue_title=title,
        issue_url="",
        repo_name="charlesreid1/centillion-search-demo",
        github_user="charlesreid1",
        content="Hello world! This is some content."
    )
