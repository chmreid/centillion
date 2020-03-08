"""Defines several Github doctypes"""
import logging
import typing
import datetime
from urllib.parse import urlparse
from centillion.doctypes.auth import GithubAuth
from . import get_stemming_analyzer


logger = logging.getLogger(__name__)


###################
# Utility functions
###################

def get_github_repos_list(name: str, g: typing.Any) -> typing.List[str]:
    """
    Use the config file to assemble a list of Github repositories to index.
    Each Github doctype specifies repos/orgs in the config file.
    Requires a valid Github API client g.

    :param str name: name of doctype entry in config file
    :param Github g: Github API client
    :returns: list of repository names of form {org}/{repo}
    """
    repos_list = []

    # Get list of repos for config orgs
    orgs = Config.get_github_orgs(name)
    for _, org in enumerate(orgs):
        logger.debug(f'Adding repositories for organization {org}...')
        # try/except here, if this fails try get_user()
        org = g.get_organization(this_org)
        repos = org.get_repos()
        for repo in repos:
            # Check this
            logger.debug(f' + Adding repository {repo.full_name}')
            repos_list.append(repo.full_name)

    # Get list of repos from config repos
    repos = Config.get_github_repos(self.name)
    logger.debug(f'Adding repositories...')
    for _, r in enumerate(repos):
        if '/' not in r:
            raise Exception("Error: invalid repo name specified")
        this_org, this_repo = re.split('/',r)
        try:
            org = get_organization(this_org)
            repo = org.get_repo(this_repo)
        except:
            try:
                user = g.get_user(this_org)
                repo = org.get_repo(this_repo)
            except:
                err = f"Error: could not gain access to repo {this_org}/{this_repo}"
                raise Exception(err)

        # Check this
        logger.debug(f' + Adding repository {repo.full_name}')
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
        self.access_token = Config.get_github_access_token(self.name)
        self.validate_credentials(access_token)

    def validate_credentials(self, access_token):
        if self.g == None:
            self.g = Github(access_token)


def GithubIssuePRDoctype(GithubBaseDoctype):
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
        issue_title = fields.TEXT(stored=True, field_boost=100.0),
        issue_url = fields.ID(stored=True),
        repo_name = fields.TEXT(stored=True),
        repo_url = fields.ID(stored=True),
        github_user = fields.TEXT(stored=True),
        content = fields.TEXT(stored=True, analyzer=get_stemming_analyzer())
    )

    def get_remote_list(self) -> typing.List[typing.Any]:
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Github types use the Github URL for the search index ID.

        :returns: list of tuples of the form:
                  (last-modified-date, id)
                  where last-modified-date is a datetime object
                  and id is a string (search index id).
        """
        name = self.name
        g = self.g

        # This stores our (last-modified-date, id) tuples
        remote_list = []

        # Iterate over each repo and store all keys + modified date
        repos_list = get_repos_list(name, g)
        for repo_name in repos_list:
            repo = g.get_repo(repo_name)

            # Iterate over issues and PRs, adding to list
            for get in [repo.get_issues, repo.get_pulls]:
                for state in ['open', 'closed']:
                    items = repo.get(state=state)
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
        g = self.g

        # The doc_id is the Github URL, turn it into a PyGithub object
        p = urlparse(doc_id)
        path_pieces = p.path.split('/')

        # Get repo reference
        repo_name = "/".join(path_pieces[1:3])
        repo_url = f"https://github.com/{repo_name}"
        repo = g.get_repo(repo_name)

        # Get issue/PR reference (get_issue and get_pull are interchangeable!)
        number = int(path_pieces[-1])
        item = g.get_pull(number)

        msg = f"Indexing issue {repo_name}#{number}"
        logging.info(msg)

        content = extract_issue_pr_contents(item)

        doc = dict(
            id = doc_id,
            kind = self.doctype,
            created_time = item.created_at,
            modified_time = item.updated_at,
            indexed_time = datetime.datetime.now(),
            name = item.title,
            issue_title = item.title,
            issue_url = item.html_url,
            repo_name = repo_name,
            repo_url = repo_url,
            github_user = item.user.login,
            content = content
        )

        return doc


    def extract_issue_pr_content(self, issue) -> str:
        """
        Given a PyGithub Issue/PullRequest object, extract the content
        of the issue/PR, including original body + all comments.

        :param issue: PyGithub Issue/PullRequest
        :returns: a string containing the contents of the issue/PR
        """
        content = ""

        if issue is None or issue.body is None:
            return content

        # Body first
        try:
            content = issue.body.rstrip()
            content += "\n"
        except AttributeError:
            pass

        # Comments second
        if(issue.comments > 0):
            try:
                comments = issue.get_comments()
                for comment in comments:
                    try:
                        content += comment.body.rstrip()
                    except AttributeError:
                        pass
                    content += "\n"
            except GithubException:
                err = f"Error: could not get comments for issue {repo_name}#{number}"
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
    schema = {}

    def get_remote_list(self):
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Github types use the Github URL for the search index ID.

        :returns: list of tuples of the form:
                  (last-modified-date, id)
                  where last-modified-date is a datetime object
                  and id is a string (search index id).
        """
        repos_list = get_repos_list(self.name, self.g)

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        pass


class GithubMarkdownDoctype(GithubBaseDoctype):
    doctype = "github_markdown"
    """
    Defines a Github markdown file doctype.
    This indexes the content of all Markdown files in Github repos.
    """
    schema = {}

    def get_remote_list(self) -> typing.List[typing.Any]:
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Github types use the Github URL for the search index ID.

        :returns: list of tuples of the form:
                  (last-modified-date, id)
                  where last-modified-date is a datetime object
                  and id is a string (search index id).
        """
        repos_list = get_github_repos_list(self.name, self.g)

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        pass
