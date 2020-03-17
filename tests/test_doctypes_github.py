import typing
import unittest
from unittest import mock
from github import Github  # GithubException

from centillion.config import Config
from centillion.doctypes.doctype import Doctype
from centillion.doctypes.github import (
    GithubBaseDoctype,
    GithubIssuePRDoctype,
    GithubFileDoctype,
    GithubMarkdownDoctype,
    get_gh_file_url,
    convert_gh_file_html_url_to_raw_url,
    get_repo_branch_from_file_url,
    get_repo_name_from_url,
    get_issue_pr_no_from_url,
    get_pygithub_branch_refs,
    get_github_repos_list,
)
from centillion.error import CentillionException

from .context import TempCentillionConfig
from .decorators import standalone_test, integration_test
from .mixins import (ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin)


# List of Github doctypes (excluding base type)
# (Integration tests should include one credential per doctype in this list in config file)
GITHUB_DOCTYPES = ["github_issue_pr", "github_file", "github_markdown"]

# NOTE: add test repo names/branches/head commit info


@standalone_test
class GithubDoctypeUtilsTest(unittest.TestCase):
    """
    Check utilities from the Github Doctype class.
    Integration tests require use of PyGithub API.
    """

    def test_gh_url_utils(self):
        repo_name = "chmreid/centillion"
        branch_name = "public"
        repo_path = "src/__init__.py"

        # get_gh_file_url
        u = f"https://github.com/{repo_name}/blob/{branch_name}/{repo_path}"
        self.assertEqual(get_gh_file_url(repo_name, branch_name, repo_path), u)

        # convert_gh_file_html_url_to_raw_url
        r = f"https://raw.githubusercontent.com/{repo_name}/{branch_name}/{repo_path}"
        self.assertEqual(convert_gh_file_html_url_to_raw_url(u), r)

        # get_repo_branch_from_file_url
        result_repo, result_branch, result_path = get_repo_branch_from_file_url(u)
        self.assertEqual(result_repo, repo_name)
        self.assertEqual(result_branch, branch_name)
        self.assertEqual(result_path, repo_path)

        # get_repo_name_from_url
        us = [
            f"https://github.com/{repo_name}/blob/{branch_name}/{repo_path}",
            f"https://github.com/{repo_name}",
            f"https://github.com/{repo_name}/issues",
            f"https://github.com/{repo_name}/pulls/1",
        ]
        for url in us:
            self.assertEqual(get_repo_name_from_url(url), repo_name)

        # get_issue_pr_no_from_url
        us = [
            f"https://github.com/{repo_name}/issues/14",
            f"https://github.com/{repo_name}/pulls/1024",
            f"https://github.com/{repo_name}/issues/1",
            f"https://github.com/{repo_name}/issues/44",
        ]
        nums = [14, 1024, 1, 44]
        for url, num in zip(us, nums):
            self.assertEqual(get_issue_pr_no_from_url(url), num)


class GithubDoctypePyGithubUtilsTest(unittest.TestCase):
    """
    Check utilities from the Github Doctype class
    that use a PyGithub API instance.

    At some point we will have a mocked standalone test,
    but for now make this an integration test.

    Integration test decorator needs to load Config with
    travis integration test credentials file so that Config
    class is all set to go.
    """

    @standalone_test
    def test_pygithub_utils_standalone(self):
        """
        Use (mocked) credentials to create (mocked) API instance,
        and use it to test the PyGithub utils.
        """
        # Assemble a mock Github API class
        class MockedCommit(object):
            sha = "0000000"

        class MockedBranch(object):
            name = ""
            commit = MockedCommit()

            def __init__(self, name):
                self.name = name

        class MockedRepo(object):
            full_name = ""

            def __init__(self, full_name):
                self.full_name = full_name

            def get_branch(self, branch_name):
                return MockedBranch(branch_name)

        class MockedGithub(object):
            """Define a barebones mocked Github API class, with sub-mocked classes"""

            def get_repo(self, repo_name):
                return MockedRepo(repo_name)

        repo_name = ""
        branch_name = ""
        g = MockedGithub()

        # test get_pygithub_branch_refs
        (repo, branch, head_commit) = get_pygithub_branch_refs(repo_name, branch_name, g)
        head_sha = "0000000"

        self.assertEqual(repo.full_name, repo_name)
        self.assertEqual(branch.name, branch_name)
        self.assertEqual(head_commit.sha, head_sha)

    @integration_test
    def test_pygithub_utils_integration(self):
        """
        Use (real) integration credentials to create (real) API instance,
        and use it to test the PyGithub utils.
        """
        doctypes_names_map = Config.get_doctypes_names_map()
        for doctype, names in doctypes_names_map.items():
            if doctype not in GITHUB_DOCTYPES:
                continue

            name = names[0]
            config = Config.get_doctype_config(name)
            access_token = config["access_token"]

            repo_name = "chmreid/centillion"
            branch_name = "public"
            g = Github(access_token)

            # test get_pygithub_branch_refs
            (repo, branch, head_commit) = get_pygithub_branch_refs(repo_name, branch_name, g)
            centillion_head_sha = "91e64330ad2881ff19253d54992ae989bc3a67ff"

            self.assertEqual(repo.full_name, repo_name)
            self.assertEqual(branch.name, branch_name)
            self.assertEqual(head_commit.sha, centillion_head_sha)


class GithubDoctypeTest(ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin):
    """
    Test Github doctypes.

    Note that because we switch between standalone and integration tests,
    we shouldn't be storing many (any?) class variables shared across methods.
    """

    @standalone_test
    def test_doctypes(self):
        """Test the doctype attribute of each Github doctype"""
        self.assertEqual(GithubBaseDoctype.doctype, "github_base")
        self.assertEqual(GithubIssuePRDoctype.doctype, "github_issue_pr")
        self.assertEqual(GithubFileDoctype.doctype, "github_file")
        self.assertEqual(GithubMarkdownDoctype.doctype, "github_markdown")

    @standalone_test
    def test_consistent_schemas(self):
        """Test that all Github document type schemas are consistent with one another"""
        self.check_consistent_schemas(GITHUB_DOCTYPES)

    @standalone_test
    def test_github_base_doctype(self):
        """Test the GithubBaseDoctype constructor, mocking the Github API creation/credentials validation step"""
        # with mock.patch("centillion.doctypes.github.Github") as gh:
        #     GithubBaseDoctype(name)
        #
        # Above assumes there is no cross-checking with config file credentials section
        pass

    @integration_test
    def test_github_doctype_constructors(self):
        """Test the constructor of each Github doctype with (real) integration credentials"""
        doctypes_names_map = Config.get_doctypes_names_map()
        self.check_doctype_constructors(GITHUB_DOCTYPES, doctypes_names_map)

    @integration_test
    def test_github_doctype_constructors_invalid_credentials(self):
        """Test that Github Doctype constructors passed invalid credentials will fail"""

        def get_invalid_config(name, doctype):
            """Private utility function to create an invalid config dict"""
            return {
                "doctypes": [{
                    "name": name,
                    "doctype": doctype,
                    "access_token": "invalid-access-token",
                    "repos": [
                        "charlesreid1/centillion-search-demo"
                    ]
                }]
            }

        # Set invalid credentials and ensure validate credentials method catches it
        names_doctypes = [
            ("invalid_config_gh_issue_pr", "github_issue_pr"),
            ("invalid_config_gh_file", "github_file"),
            ("invalid_config_gh_md", "github_markdown")
        ]
        for name, doctype in names_doctypes:
            with TempCentillionConfig(get_invalid_config(name, doctype)) as config_file:
                with self.assertRaises(CentillionException):
                    self.assertEqual(Config._CONFIG_FILE, config_file)
                    registry = Doctype.get_registry()
                    DoctypeCls = registry[doctype]
                    DoctypeCls(name)

    @standalone_test
    def test_github_doctype_constructors_invalid(self):
        # Check that invalid inputs to constructor will not work
        pass

    @standalone_test
    def test_render_search_result(self):
        doctype_classes = self._get_github_doctype_classes()

        # Mock whoosh search result class - extend dict so you can use ['key']
        class MockWhooshResult(dict):
            # Any non-schema fields used?
            pass

        # We are probably gonna have to hard-code one of every doctype
        # Set each field to something sensible
        # Pass it to render_search_result()
        # Get back a SearchResult

    @standalone_test
    def test_render_search_result_invalid(self):
        # Test invalid inputs to render search result
        pass

    @standalone_test
    def test_get_jinja_template(self):
        """Test the Jinja template returned by each Github doctype"""
        # Turn a list of doctype labels into a list of doctype classes
        doctype_classes = self._get_github_doctype_classes()
        required_strings = ['<div class="url">', '<div class="markdown-body">']
        for DoctypeCls in doctype_classes:
            for required_string in required_strings:
                self.assertIn(required_string, DoctypeCls.get_jinja_template())

    @standalone_test
    def test_render_matches_jinja(self):
        """
        Confirm that the SearchResult object resulting from render_search_result is consistent
        with the variables used in the Jinja template.
        """
        # Create a doctype instance for each registered doctype
        # Get the jinja2schema from that doctype
        # Use jinja2schema to extract jinja variables used in template
        # For each attribute of search_result,
        # Check that SearchResult has that attribute
        pass

    @integration_test
    def test_get_remote_list(self):
        doctypes_names_map = Config.get_doctypes_names_map()
        self.check_doctype_remote_list(GITHUB_DOCTYPES, doctypes_names_map)

    @integration_test
    def test_github_issues_prs(self):
        """Test the get_by_id (and get_schema) methods for the Github issue/PR doctype"""
        this_doctype = "github_issue_pr"
        doctypes_names_map = Config.get_doctypes_names_map()
        names = doctypes_names_map[this_doctype]
        name = names[0]
        doctype = GithubIssuePRDoctype(name)

        # Test an issue
        issue_id = "https://github.com/charlesreid1/centillion-search-demo/issues/1"
        doc = doctype.get_by_id(issue_id)
        self.assertEqual(issue_id, doc["id"])
        self.assertEqual(issue_id, doc["issue_url"])
        self.assertEqual("Seattle drivers", doc["name"])
        self.assertEqual("Seattle drivers", doc["issue_title"])
        self.assertIn("charlesreid1", doc["github_user"])
        self.assertEqual("charlesreid1/centillion-search-demo", doc["repo_name"])
        self.assertIn("certain Seattle drivers", doc["content"])

        # Test a pull request (TBA)

    @integration_test
    def test_github_files(self):
        """Test the get_by_id (and get_schema) methods for the Github file doctype"""
        pass

    @integration_test
    def test_github_markdown(self):
        """Test the get_by_id (and get_schema) methods for the Github markdown doctype"""
        pass

    def _get_github_doctype_classes(self) -> typing.List[object]:
        """
        Given a list of strings of doctype classes, turn those into
        references to the actual class using the Doctype Registry.
        """
        doctype_classes = []
        registry = Doctype.get_registry()
        for doctype in GITHUB_DOCTYPES:
            doctype_classes.append(registry[doctype])
        return doctype_classes


if __name__ == "__main__":
    unittest.main()
