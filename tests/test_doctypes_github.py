import typing
import unittest
import itertools
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

from .decorators import standalone_test, integration_test


# List of Github doctypes (excluding base type)
# (Integration tests should include one credential per doctype in this list in config file)
GITHUB_DOCTYPES = ["github_issue_pr", "github_file", "github_markdown"]


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


@integration_test
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

    creds_name: typing.Optional[str] = None
    g: typing.Optional[Github] = None

    @classmethod
    def setUpClass(cls):
        # Normally we don't access the config directly,
        # but doing so is convenient for these tests.
        #
        # Note that the integration test decorator will
        # ste the config file to the integration test
        # config file.
        for cred in Config._CONFIG["doctypes"]:
            if cred["doctype"].startswith("github"):
                # Test config should only need one github access token
                cls.creds_name = cred["name"]
                cls.g = Github(cred["access_token"])
                break

    def test_pygithub_utils(self):
        repo_name = "chmreid/centillion"
        branch_name = "public"

        # get_pygithub_branch_refs
        (repo, branch, head_commit) = get_pygithub_branch_refs(repo_name, branch_name, self.g)
        centillion_head_sha = "91e64330ad2881ff19253d54992ae989bc3a67ff"
        self.assertEqual(head_commit.sha, centillion_head_sha)
        self.assertEqual(repo.full_name, repo_name)

        # get_github_repos_list
        correct_list = [repo_name]
        repos_list = get_github_repos_list(self.creds_name, self.g)
        self.assertEqual(repos_list, correct_list)


@standalone_test
class GithubDoctypeStandaloneTest(unittest.TestCase):
    """
    Do a standalone test of Github doctypes.
    This does not make any real API calls or require real tokens.
    """

    doctypes_names_map = Config.get_doctypes_names_map()

    def test_doctypes(self):
        self.assertEqual(GithubBaseDoctype.doctype, "github_base")
        self.assertEqual(GithubIssuePRDoctype.doctype, "github_issue_pr")
        self.assertEqual(GithubFileDoctype.doctype, "github_file")
        self.assertEqual(GithubMarkdownDoctype.doctype, "github_markdown")

    def test_consistent_schemas(self):
        """Test that all Github document type schemas are consistent with one another"""
        # Generate all pairwise combinations
        for doctype, other_doctype in itertools.combinations(GITHUB_DOCTYPES, 2):
            msg = f"Check doctype schemas {doctype} and {other_doctype} are consistent"
            with self.subTest(msg):

                # Get class refs from doctype registry
                registry = Doctype.get_registry()
                DoctypeCls = registry[doctype]
                OtherDoctypeCls = registry[other_doctype]

                # Get credentials name
                name = self.doctypes_names_map[doctype][0]
                other_name = self.doctypes_names_map[other_doctype][0]

                # Get schemas
                doctype_schema = DoctypeCls(name).schema
                other_doctype_schema = OtherDoctypeCls(other_name).schema

                # Get shared keys
                doctype_schema_keys = set(doctype_schema.keys())
                other_doctype_schema_keys = set(other_doctype_schema.keys())
                shared_schema_keys = doctype_schema_keys.intersection(other_doctype_schema_keys)

                # Verify types of shared schema keys are consistent
                for shared_key in shared_schema_keys:
                    this_type = type(doctype_schema[shared_key])
                    other_type = type(other_doctype_schema[shared_key])
                    self.assertEqual(this_type, other_type)

    def test_github_base_doctype(self):
        # Mock centillion.doctypes.github.Github first
        # Mock config file, fake credentials
        # g = GithubBaseDoctype('name')
        pass


@integration_test
class GithubDoctypeIntegrationTest(unittest.TestCase):
    """
    Do an integration test of Github doctypes.
    All API calls are real, all API tokens are for real accounts.
    """

    # Map of doctype labels to credential names
    doctypes_names_map: typing.Optional[typing.Dict] = dict()

    @classmethod
    def setUpClass(cls):
        # Get list of doctypes actually in config file
        doctypes_in_config = Config.get_doctypes()
        for doctype in GITHUB_DOCTYPES:
            # Make sure required doctypes are in config file
            if doctype not in doctypes_in_config:
                raise Exception(f"Error: credentials for {doctype} not in config file")
            # Get the creds name associated with each doctype
            for cred in Config._Config["doctypes"]:
                if cred["doctype"] == doctype:
                    cls.doctypes_names_map[doctype] = cred["name"]
                    break

    def test_github_doctypes(self):
        """Test the constructor and the get_remote_list function for each usable Github doctype"""
        for doctype, name in self.doctypes_names_map.items():
            # Doctype gives name, name is passed to constructor.
            # Doctype gives class ref via registry.
            registry = Doctype.get_registry()
            DoctypeCls = registry[doctype]

            # Make the doctype class.
            # This step gets creds from config file and validates them.
            doctype = DoctypeCls(name)

            # get_remote_list
            rl = doctype.get_remote_list()
            self.assertTrue(len(rl) > 0)
            # Note: Need to look into short-circuiting the list functionality
            # during tests. Config class can help during tests.
            # Or add argument to get_remote_list.

            # get_by_id (skip, requires doctype-specific implementation)
            # get_schema (skip, check when checking get_by_id)

    def test_github_issues_prs(self):
        """Test get_by_id and get_schema for GithubIssuesPRsDoctype class"""
        name = self.doctypes_names_map["github_issue_pr"]
        doctype = GithubIssuePRDoctype(name)
        doc_id = "https://github.com/charlesreid1/centillion-search-demo/issues/1"
        doc = doctype.get_by_id(doc_id)
        self.assertEqual(doc_id, doc["id"])
        self.assertEqual(doc_id, doc["issue_url"])
        self.assertEqual("Seattle drivers", doc["name"])
        self.assertEqual("Seattle drivers", doc["issue_title"])
        self.assertIn("charlesreid1", doc["github_user"])
        self.assertEqual("charlesreid1/centillion-search-demo", doc["repo_name"])
        self.assertIn("certain Seattle drivers", doc["content"])


if __name__ == "__main__":
    unittest.main()
