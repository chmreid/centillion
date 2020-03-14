"""Defines several Github doctypes"""
import os
import re
import logging
import typing
import requests
import base64
import datetime
from whoosh import fields
from urllib.parse import urlparse
from github import Github, GithubException

from . import get_stemming_analyzer
from .doctype import Doctype
from ..config import Config
from ..error import CentillionConfigException


logger = logging.getLogger(__name__)


###################
# Utility functions
###################


def get_gh_file_url(repo_name: str, branch_name: str, repo_path: str) -> str:
    """
    Assemble a Github HTML URL to a file on a branch of a Github repo.

    :param repo_name: full repo name in the form {1}/{2}
    :param branch_name: name of the branch this file is on
    :param repo_path: full path and filename of the file, from the root of the repo
    :returns: Github HTML URL that leads to the file on the branch of the repo
    """
    return f"https://github.com/{repo_name}/blob/{branch_name}/{repo_path}"


def convert_gh_file_html_url_to_raw_url(gh_file_html_url: str) -> str:
    """
    Return the Github raw URL for a given a Github HTML URL to a file on a branch of a Github repo.

    :param gh_file_html_url: Github HTML URL to the file on the branch of the repo
    :returns: Github raw URL that leads to the file on the branch of the repo
    """
    u = re.sub("github.com", "raw.githubusercontent.com", gh_file_html_url, 1)
    u = re.sub("blob/", "", u, 1)
    return u


def get_repo_branch_from_file_url(gh_url: str) -> typing.Tuple[str, str, str]:
    """
    Extract the full repo name, branch name, and repo path from a Github file HTML URL.

    :param gh_url: Github HTML URL of the form https://github.com/{1}/{2}/blob/{3}/...
    :returns: tuple with three strings (full repo name, branch name, repo path)
    """
    p = urlparse(gh_url)
    path_pieces = p.path.split("/")
    repo_name = "/".join(path_pieces[1:3])
    branch_name = path_pieces[4]
    repo_path = "/".join(path_pieces[5:])
    return (repo_name, branch_name, repo_path)


def get_repo_name_from_url(gh_url: str) -> str:
    """
    Extract the full repo name from a Github HTML URL.

    :param gh_url: Github HTML URL of the form https://github.com/{1}/{2}/...
    :returns: full repo name
    """
    p = urlparse(gh_url)
    path_pieces = p.path.split("/")
    repo_name = "/".join(path_pieces[1:3])
    return repo_name


def get_issue_pr_no_from_url(gh_url: str) -> int:
    """
    Extract the issue/PR number from a Github HTML URL.

    :param gh_url: Github HTML URL of the form https://github.com/{1}/{2}/.../#
    :returns: int corresponding to PR/issue number
    """
    p = urlparse(gh_url)
    path_pieces = p.path.split("/")
    number = int(path_pieces[-1])
    assert number > 0
    return number


def get_pygithub_branch_refs(repo_name: str, branch_name: str, g):
    """
    Given a repo and branch name, return PyGithub objects referring to
    the repo, the branch, and the head commit of the branch, in a tuple.

    :param repo_name: full name of repository of form {1}/{2}
    :param branch_name: name of branch
    :param g: Github API client
    :returns: tuple of form (repo_obj, branch_obj, head_commit_obj)
    """
    repo = g.get_repo(repo_name)
    branch = repo.get_branch(branch_name)
    head_commit = branch.commit
    return (repo, branch, head_commit)


def get_github_repos_list(name: str, g) -> typing.List[str]:
    """
    Use the config file to assemble a list of Github repositories to index.
    Each Github doctype specifies repos/orgs in the config file.
    Requires a valid Github API client g.

    :param str name: name of doctype entry in config file
    :param g: Github API client
    :returns: list of repository names of form {org}/{repo}
    """
    repos_list = []

    def _get_config_github_orgs(config):
        """Extract the list of github orgs from a config credentials section"""
        return config['orgs']

    def _get_config_github_repos(config):
        """Extract the list of github repos from a config credentials section"""
        return config['repos']

    # Get list of repos for config orgs
    config = Config.get_doctype_config(name)
    orgs = _get_config_github_orgs(config)
    for _, this_org in enumerate(orgs):
        logger.debug(f"Adding repositories for Github org {this_org}...")
        try:
            org = g.get_organization(this_org)
        except GithubException:
            try:
                org = g.get_user(this_org)
            except GithubException:
                err = f"Error: could not gain access to Github org/user {this_org}"
                raise Exception(err)
        repos = org.get_repos()
        for repo in repos:
            # Check this
            logger.debug(f" + Adding repository {repo.full_name}")
            repos_list.append(repo.full_name)

    # Get list of repos from config repos
    repos = _get_config_github_repos(name)
    logger.debug(f"Adding repositories...")
    for _, r in enumerate(repos):
        if "/" not in r:
            raise Exception("Error: invalid repo name specified")
        this_org, this_repo = re.split("/", r)
        try:
            org = g.get_organization(this_org)
            repo = org.get_repo(this_repo)
        except GithubException:
            try:
                user = g.get_user(this_org)
                repo = user.get_repo(this_repo)
            except GithubException:
                err = f"Error: could not gain access to repo {this_org}/{this_repo}"
                raise Exception(err)

        # Check this
        logger.debug(f" + Adding repository {repo.full_name}")
        repos_list.append(repo.full_name)

    return repos_list


#################
# Doctype classes
#################

class GithubBaseDoctype(Doctype):
    doctype = "github_base"
    """
    Defines a base Github document type.
    All GithubBaseDoctype subclasses will use
    the same kind of API instance, so we have a
    common validation method, etc.
    This base class only defines:
    - constructor
    - validate credentials
    """
    name: typing.Optional[str] = None
    g: typing.Optional[Github] = None

    def __init__(self, *args, **kwargs):
        """
        Constructor is only passed the name of the credentials.
        Constructor uses name to get Github credentials, and all other
        options set in the Config file for this set of credentials.
        """
        self.name = args[0]
        doctype_config = Config.get_doctype_config(self.name)
        try:
            self.access_token = doctype_config['access_token']
        except KeyError:
            raise CentillionConfigException(
                f"Error: {self.doctype} credentials section does not contain access_token"
            )
        self.validate_credentials(self.access_token)

    def validate_credentials(self, access_token):
        if self.g is None:
            self.g = Github(access_token)


class GithubIssuePRDoctype(GithubBaseDoctype):
    doctype = "github_issue_pr"
    """
    Defines a Github pull request/issue doctype.
    This indexes the contents of the threads of each
    issue and pull request in Github repos.

    Subclasses of GithubBaseDoctype must define the following:
    - schema (class attribute)
    - get_remote_list: list of remote document IDs and last modified date
    - get_by_id: get document by index ID
    - search result template (static)
    """
    schema = dict(
        issue_title=fields.TEXT(stored=True, field_boost=100.0),
        issue_url=fields.ID(stored=True),
        repo_name=fields.TEXT(stored=True),
        github_user=fields.KEYWORD(stored=True, lowercase=True, commas=True),
        content=fields.TEXT(stored=True, analyzer=get_stemming_analyzer()),
    )

    def get_remote_list(self) -> typing.List[typing.Tuple[datetime.datetime, str]]:
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Github types use the Github URL for the search index ID.

        :returns: list of (last_modified_date, issue_pr_url) tuples
                  (types are datetime.datetime and str)
        """
        name = self.name
        g = self.g

        # Return value: list of (last_modified_date, issue_pr_url) tuples
        remote_list = []

        # Iterate over each repo and store all keys + modified date
        repos_list = get_github_repos_list(name, g)
        for repo_name in repos_list:
            repo = g.get_repo(repo_name)

            # Iterate over issues and PRs, adding to list
            for get in [repo.get_issues, repo.get_pulls]:
                for state in ["open", "closed"]:
                    items = get(state=state)
                    for _, item in enumerate(items):
                        # Add an item (issue/PR) to the list
                        key = item.html_url
                        date = item.updated_at
                        remote_list.append((date, key))

        return remote_list

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its search index id
        (Github URL for all Github doctypes), and return an
        item to the search index matching the index schema.
        """
        name = self.name
        g = self.g

        # Get repo reference
        repo_name = get_repo_name_from_url(doc_id)

        # Verify this is in the config file list of repos
        repos_list = get_github_repos_list(name, g)
        if repo_name not in repos_list:
            raise CentillionConfigException(f"Error: Repo {repo_name} not listed in config section {self.name}")

        # Get issue/PR reference (get_issue and get_pull are interchangeable!)
        number = get_issue_pr_no_from_url(doc_id)
        repo = g.get_repo(repo_name)
        item = repo.get_pull(number)

        msg = f"Indexing issue {repo_name}#{number}"
        logger.info(msg)

        user_list = self._extract_issue_pr_user_list(item)
        content = self._extract_issue_pr_content(item)

        doc = dict(
            id=doc_id,
            kind=self.doctype,
            created_time=item.created_at,
            modified_time=item.updated_at,
            indexed_time=datetime.datetime.now(),
            name=item.title,
            issue_title=item.title,
            issue_url=item.html_url,
            repo_name=repo_name,
            github_user=user_list,
            content=content,
        )

        return doc

    def _extract_issue_pr_user_list(self, item) -> str:
        """
        Given a PyGithub Issue/PullRequest object, extract a list of
        Github users related to the item (creator, commentors, assignees, etc.)

        :param item: Github Issue/PullRequest to extract user list from
        :returns: comma-separated list of Github user handles related to this issue/PR
        """
        user_list = []

        user_list.append(item.user.login)
        for assignee in item.assignees:
            user_list.append(assignee.login)
        if item.comments > 0:
            try:
                comments = item.get_comments()
                for comment in comments:
                    user_list.append(comment.user.login)
            except GithubException:
                pass

        return ",".join(user_list)

    def _extract_issue_pr_content(self, item) -> str:
        """
        Given a PyGithub Issue/PullRequest object, extract the content
        of the issue/PR, including original body + all comments.

        :param issue: PyGithub Issue/PullRequest
        :returns: a string containing the contents of the issue/PR
        """
        content = ""

        if item is None or item.body is None:
            return content

        # Body first
        try:
            content = item.body.rstrip()
            content += "\n"
        except AttributeError:
            pass

        # Comments second
        if item.comments > 0:
            try:
                comments = item.get_comments()
                for comment in comments:
                    try:
                        content += comment.body.rstrip()
                        content += "\n"
                    except AttributeError:
                        pass
            except GithubException:
                err = f"Error: could not get comments for issue/PR"
                logger.error(err)
                pass

        return content


class GithubFileDoctype(GithubBaseDoctype):
    doctype = "github_file"
    """
    Defines a Github file doctype.
    This indexes the names/metadata of all files in Github repos.
    (...every branch?? of every repo??)
    """
    schema = dict(
        file_name=fields.TEXT(stored=True, field_boost=100.0),
        file_url=fields.ID(stored=True),
        repo_path=fields.TEXT(stored=True),
        repo_name=fields.TEXT(stored=True),
        github_user=fields.KEYWORD(stored=True, lowercase=True, commas=True),
    )

    def get_remote_list(self) -> typing.List[typing.Tuple[datetime.datetime, str]]:
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Github types use the Github URL for the search index ID.

        :returns: list of (last_modified_date, issue_pr_url) tuples
                  (types are datetime.datetime and str)
        """
        name = self.name
        g = self.g

        # Return value: list of (last_modified_date, file_url) tuples
        remote_list = []

        repos_list = get_github_repos_list(name, g)
        for repo_name in repos_list:
            repo = g.get_repo(repo_name)

            # What about other branches?
            # What about other commits?

            # To iterate over all files, we need a git tree, which requires a commit reference.
            # Get head commit of default branch
            try:
                branch_name = repo.default_branch
                default_branch = repo.get_branch(branch_name)
                head_commit = default_branch.commit
                sha = head_commit.sha
            except GithubException:
                err = (
                    f"Error: could not fetch commits from default branch of repository {repo_name}"
                )
                logger.error(err)
                continue

            # Get all the docs
            tree = repo.get_git_tree(sha=sha, recursive=True)
            docs = tree.raw_data["tree"]
            msg = "Parsing file ids from repository %s" % (repo_name)
            logger.info(msg)
            for item in docs:
                # Split document path into its useful parts
                fpath = item["path"]
                _, fname = os.path.split(fpath)
                _, fext = os.path.splitext(fpath)
                fpathpieces = fpath.split("/")
                # NOTE:
                # This method should be redefined to filter on specific file types
                # when defining a new Github file doctype
                ignore_file = self._ignore_file_check(fname, fext, fpathpieces)
                if not ignore_file:
                    # PyGithub doesn't provide an HTML URL for files,
                    # but we can assemble one ourselves.
                    key = get_gh_file_url(repo_name, branch_name, item["path"])
                    date = head_commit.commit.author.date
                    remote_list.append((date, key))

        return remote_list

    def _ignore_file_check(self, fname: str, fext: str, fpathpieces: typing.List[str]) -> bool:
        """
        Return True if this file should be ignored when assembling the remote list of files.
        Subclasses can override this method to return remote lists but with filtered filetypes.
        They should check the result of super()._ignore_file_check(...) first.

        :param fname: name of the file
        :param fext: extension of the file
        :param pathpieces: pieces of the relative repository path of the file
        :returns bool: return True if this file should be ignored when compiling the list of remote
        """
        # Ignore anything whose name starts with . or _
        if fname[0] == "." or fname[0] == "_":
            return True

        for piece in fpathpieces:
            if piece[0] == "." or piece[0] == "_":
                return True

        return False

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        name = self.name
        g = self.g

        # Extract labels from URL
        repo_name, branch_name, repo_path = get_repo_branch_from_file_url(doc_id)
        file_name = repo_path.split("/")[-1]

        # Verify this is in the config file list of repos
        repos_list = get_github_repos_list(name, g)
        if repo_name not in repos_list:
            raise CentillionConfigException(f"Error: Repo {repo_name} not listed in config section {self.name}")

        # Get PyGithub objects from labels
        repo, branch, head_commit = get_pygithub_branch_refs(repo_name, branch_name, g)

        msg = f"Indexing file {repo_path} in repo {repo_name}"
        logger.info(msg)

        doc = dict(
            id=doc_id,
            kind=self.doctype,
            created_time=None,
            modified_time=head_commit.commit.author.date,
            indexed_time=datetime.datetime.now(),
            name=file_name,
            file_name=file_name,
            file_url=doc_id,
            repo_path=repo_path,
            github_user=head_commit.commit.author.login,
        )

        return doc


class GithubMarkdownDoctype(GithubFileDoctype):
    doctype = "github_markdown"
    """
    Defines a Github markdown file doctype.
    This indexes the content of all Markdown files in Github repos.
    """
    schema = dict(
        **GithubFileDoctype.schema,
        content=fields.TEXT(stored=True, analyzer=get_stemming_analyzer()),
    )

    def _ignore_file_check(self, fname: str, fext: str, fpathpieces: typing.List[str]) -> bool:
        """
        Return True if this file should be ignored when assembling the remote list of files.
        Extends GithubFileDoctype._ignore_file_check

        :param fname: name of the file
        :param fext: extension of the file
        :param pathpieces: pieces of the relative repository path of the file
        :returns bool: return True if this file should be ignored when compiling the list of remote
        """
        if super()._ignore_file_check(fname, fext, fpathpieces):
            return True

        if fext not in [".md", ".markdown"]:
            return True

        return False

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        name = self.name
        g = self.g

        # Extract labels from URL
        repo_name, branch_name, repo_path = get_repo_branch_from_file_url(doc_id)
        file_name = repo_path.split("/")[-1]

        # Verify this is in the config file list of repos
        repos_list = get_github_repos_list(name, g)
        if repo_name not in repos_list:
            raise CentillionConfigException(f"Error: Repo {repo_name} not listed in config section {self.name}")

        # Get PyGithub objects from labels
        repo, _, head_commit = get_pygithub_branch_refs(repo_name, branch_name, g)

        msg = f"Indexing Markdown file {repo_path} in repo {repo_name}"
        logger.info(msg)

        content = self._extract_markdown_content(repo, head_commit, repo_path)

        doc = dict(
            id=doc_id,
            fingerprint=head_commit.sha,
            kind=self.doctype,
            created_time=None,
            modified_time=head_commit.commit.author.date,
            indexed_time=datetime.datetime.now(),
            name=file_name,
            file_name=file_name,
            file_url=doc_id,
            repo_path=repo_path,
            github_user=head_commit.commit.author.login,
            content=content,
        )

        return doc

    def _extract_markdown_content(self, repo, head_commit, repo_path):
        """
        Extract the content of a markdown file located at repo_path in repo at commit head_commit.

        :param repo: PyGithub Repository object
        :param head_commit: PyGithub Commit object corresponding to head commit of branch of interest
        :param repo_path: relative path in the repo to the markdown file of interest
        """
        content = ""

        # Get a reference to the tree to get a list of files + URLs to access their contents
        repo_name = repo.full_name
        sha = head_commit.sha
        tree = repo.get_git_tree(sha=sha, recursive=True)
        docs = tree.raw_data["tree"]

        # Find the doc we are interested in
        doc = None
        for d in docs:
            if d["path"] == repo_path:
                doc = d
        if doc is None:
            err = f"Error: No file found matching {repo_path} in repo {repo_name} commit {sha}."
            logger.error(err)
            return content

        # The API URL will be a JSON document whose "content" field has the document contents.
        # Make a request to the API URL and decode the result. Include headers for private repos!
        # Useful: https://bit.ly/2LSAflS
        headers = {"Authorization": "token %s" % (self.access_token)}
        url = doc["url"]
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            jresponse = response.json()
            try:
                binary_content = re.sub("\n", "", jresponse["content"])
                content = base64.b64decode(binary_content).decode("utf-8")
                return content
            except KeyError:
                err = f"Error: Failed to extract 'content' field from response to {url}.\n"
                err += "You probably hit the Github API rate limit."
                logger.error(err)
                return content
            else:
                err = f"Error: Failed to decode JSON from {url}. There may be a problem with authentication/headers."
                logger.error(err)
                return content
        else:
            msg = f"Error: Github returned status code {response.status_code}"
            logger.error(msg)
            logger.error(str(response))
