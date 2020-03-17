import typing


SAMPLE_GITHUB_ISSUE_PR: typing.Dict[str, str] = {
    'issue_title': '',
    'issue_url': '',
    'repo_name': '',
    'github_user': '',
    'content': '',
}

SAMPLE_GITHUB_FILE: typing.Dict[str, str] = {}

SAMPLE_GITHUB_MARKDOWN: typing.Dict[str, str] = {}

SAMPLE_GDRIVE_FILE: typing.Dict[str, str] = {}

SAMPLE_GDRIVE_DOCX: typing.Dict[str, str] = {}

INVALID_GOOGLE_CREDENTIALS: str = """
{
    "access_token": "blahblahblah",
    "client_id": "blahblahblah",
    "client_secret": "blahblahblah",
    "refresh_token": "blahblahblah",
    "token_expiry": "2000-01-01T00:00:00Z",
    "token_uri": "https://example.com",
    "user_agent": null,
    "revoke_uri": "https://example.com",
    "id_token": null,
    "token_response": {
        "access_token": "blahblahblah",
        "expires_in": 0,
        "refresh_token": "blahblahblah"
        "scope": "https://example.com",
        "token_type": "Bearer"
    },
    "scopes": ["https://example.com"],
    "token_info_uri": "https://example.com",
    "invalid": false,
    "_class": "OAuth2Credentials",
    "_module": "oauth2client.client"}
"""
