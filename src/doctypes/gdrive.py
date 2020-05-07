"""Defines several Google Drive doctypes"""
import os
import re
import codecs
import pypandoc
import requests
import subprocess
import typing
import logging
import datetime
import dateutil.parser
from whoosh import fields
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file

from .content import get_stemming_analyzer  # scrub_markdown
from .doctype import Doctype
from ..config import Config
from ..error import CentillionConfigException
from ..util import SearchResult, search_results_timestamps_datetime_to_str, is_absolute_path


logger = logging.getLogger(__name__)


###################
# Utility functions
###################


def get_gdrive_service(token_path):
    """
    This requires that the operator do the following:

    - Download client_secrets.json from API section of Google CLoud Console
    - Run scripts/prepare_gdrive.py to convert client_secrets.json to credentials.json
      (requires a one-time interactive login step)
    - Put the credentials.json file in the path specified in the centillion config file

    Then token_path above should be set to the path of credentials.json.
    It can be an absolute path,
    """
    real_token_path = find_token_path(token_path)
    store = file.Storage(real_token_path)
    creds = store.get()
    if not creds or creds.invalid:
        raise Exception("Error: invalid or missing Google Drive API credentials")
    service = build("drive", "v3", http=creds.authorize(Http()))
    return real_token_path, service.files()


def find_token_path(token_path):
    if is_absolute_path(token_path):
        # Easy case: absolute path to GDrive token
        if os.path.exists(token_path):
            return token_path
        else:
            err = f"Error: Could not find Google Drive token at absolute path {token_path}"
            raise CentillionConfigException(err)
    else:
        # Look for GDrive credentials in centillion root
        root_dir = os.path.abspath(Config.get_centillion_root())
        tproot = os.path.join(root_dir, token_path)
        if os.path.exists(tproot):
            return tproot

        # Look for GDrive credentials in config dir
        config_dir = os.path.abspath(os.path.dirname(Config.get_config_file()))
        tpconf = os.path.join(config_dir, token_path)
        if os.path.exists(tpconf):
            return tpconf

        err = f"Error: Could not find Google Drive token at relative path {token_path}"
        err += f"\nTried {tproot} and {tpconf}"
        raise CentillionConfigException(err)

#################
# Doctype classes
#################


class GDriveBaseDoctype(Doctype):
    doctype = "gdrive_base"
    """
    Defines a base Google Drive document type.

    All GDriveBaseDoctype subclasses will use
    the same API instance, so use a common constructor
    and validation method.

    This base class only defines:
    - constructor
    - validate credentials
    """
    drive = None  # type: ignore

    def __init__(self, *args, **kwargs):
        """
        Constructor is only passed the name of the credentials.
        Constructor uses name to get GDrive credentials.
        """
        self.name = args[0]
        self._parse_config()

    def _parse_config(self):
        config = Config.get_doctype_config(self.name)

        # GDrive token file "credentials.json" can live in three places:
        # 1. if token_path is an absolute path, the location given by it
        # 2. a path relative to centillion root
        # 3. a path relative to the config file dir
        tp = config["token_path"]
        logger.info(f"Doctype {self.name} using credentials file at {tp}")
        self.validate_credentials(tp)
        self.token_path = tp

    def validate_credentials(self, token_path):
        # get_gdrive_service will handle checking whether token_path exists
        if self.drive is None:
            self.token_path, self.drive = get_gdrive_service(token_path)


class GDriveFileDoctype(GDriveBaseDoctype):
    doctype = "gdrive_file"
    """
    Defines a Google Drive file filetype.
    This indexes the name/metadata of all files in a given
    Google Drive folder/location.
    """
    schema = dict(
        file_name=fields.TEXT(stored=True, field_boost=100.0),
        file_url=fields.ID(stored=True),
        mimetype=fields.TEXT(stored=True),
        owner_email=fields.TEXT(stored=True),
        owner_name=fields.TEXT(stored=True),
    )

    @classmethod
    def render_search_result(cls, whoosh_search_result):
        """
        Process whoosh search result fields to prepare them for HTML displaying.
        """
        # Turn the whoosh_search_result into something that works with Jinja template below
        result = SearchResult()
        for common_key in cls.get_common_schema():
            result[common_key] = whoosh_search_result.getattr(common_key)
        for gh_key in cls.get_schema():
            result[gh_key] = whoosh_search_result.getattr(gh_key)

        # Parse and process datetimes into strings
        search_results_timestamps_datetime_to_str(result)

        return result

    @classmethod
    def get_jinja_template(cls) -> str:
        """
        Return a string containing Jinja HTML template for rendering
        search results of this doctype. Must match schema.
        """
        template = """
                <div class="url">
                    <a class="result-title" href="{{e.url}}">{{e.title}}</a>
                    <br />
                    <span class="badge kind-badge">Google Drive File</span>
                    <br />
                    <b>Owner:</b> {{e.owner_name}} &lt;{{e.owner_email}}&gt;
                    <br/>
                    <b>Repository:</b> <a href="{{e.repo_url}}">{{e.repo_name}}</a>
                    {% if e.created_time %}
                        <br/>
                        <b>Created:</b> {{e.created_time}}
                    {% endif %}
                    {% if e.modified_time %}
                        <br/>
                        <b>Modified:</b> {{e.modified_time}}
                    {% endif %}
                </div>
                <div class="markdown-body">
                    <p>(A preview of this document is not available.)</p>
                </div>
        """
        return template

    def get_remote_map(self) -> typing.Dict[str, datetime.datetime]:
        """
        Compile a map of document IDs for documents that can be indexed
        at the remote, to their last modified date.

        Google Drive uses GDrive ID for the search index ID.

        :returns: map of gdrive_id to last_modified_date
        """
        drive = self.drive

        # Return value: map of gdrive_id to last_modified_date
        remote_map = {}

        # To iterate over all files, use the list() function of drive
        nextPageToken = None  # This is the trick to get this to work

        # Use the pager to return all the things
        while True:
            ps = 100

            # raises googleapiclient.errors.HttpError
            results = drive.list(  # type: ignore
                pageSize=ps,
                pageToken=nextPageToken,
                fields="nextPageToken, files(id, kind, createdTime, modifiedTime, mimeType, name, owners, webViewLink)",
                spaces="drive",
            ).execute()

            # results example:
            # z = {
            #     "files": [
            #         {
            #             "kind": "drive#file",
            #             "id": "1pjk3c79lBN3pTW1kNHvwlYR8_24g7Zdhu4efbt-b7c8",
            #             "name": "Crime and Punishment Chapter 1",
            #             "mimeType": "application/vnd.google-apps.document",
            #             "webViewLink":
            #             "https://docs.google.com/document/d/1pjk3c79lBN3pTW1kNHvwlYR8_24g7Zdhu4efbt-b7c8/edit?usp=drivesdk", # noqa
            #             "createdTime": "2019-02-08T06:42:43.991Z",
            #             "modifiedTime": "2019-02-08T06:45:27.588Z",
            #             "owners": [
            #                 {
            #                     "kind": "drive#user",
            #                     "displayName": "1 centillion",
            #                     "me": True,
            #                     "permissionId": "02189361238549265596",
            #                     "emailAddress": "cent17710n@gmail.com",
            #                 }
            #             ],
            #         },
            #         {
            #             "kind": "drive#file",
            #             "id": "0B2LoGxMr7f5Xc3RhcnRlcl9maWxl",
            #             "name": "Getting started",
            #             "mimeType": "application/pdf",
            #             "webViewLink": "https://drive.google.com/file/d/0B2LoGxMr7f5Xc3RhcnRlcl9maWxl/view?usp=drivesdk", # noqa
            #             "createdTime": "2019-02-08T03:00:12.209Z",
            #             "modifiedTime": "2019-02-08T03:00:12.209Z",
            #             "owners": [
            #                 {
            #                     "kind": "drive#user",
            #                     "displayName": "1 centillion",
            #                     "me": True,
            #                     "permissionId": "02189361238549265596",
            #                     "emailAddress": "cent17710n@gmail.com",
            #                 }
            #             ],
            #         },
            #     ]
            # }

            nextPageToken = results.get("nextPageToken")
            files = results.get("files", [])
            for f in files:
                fid = f["id"]
                fname = f["name"]
                fmimetype = f["mimeType"]
                ignore_file = self._ignore_file_check(fname, fmimetype)
                if not ignore_file:
                    key = fid
                    date = dateutil.parser.parse(f["modifiedTime"])
                    remote_map[key] = date

            # End pagination early for tests
            if (
                nextPageToken is None
                or os.environ.get("CENTILLION_TEST_MODE", None) == "integration"
            ):
                break

        # Note: remote_map may be an empty list!
        return remote_map

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        # uses get method: https://developers.google.com/drive/api/v3/reference/files/get
        item = self.drive.files().get(doc_id)

        doc = dict(
            id=doc_id,
            fingerprint=item["md5Checksum"],
            kind=self.doctype,
            created_time=dateutil.parser.parse(item["createdTime"]),
            modified_time=dateutil.parser.parse(item["modifiedTime"]),
            indexed_time=datetime.datetime.now().replace(microsecond=0),
            name=item["name"],
            file_name=item["name"],
            file_url=item["webViewLink"],
            mimetype=item["mimeType"],
            owner_email=item["owners"][0]["emailAddress"],
            owner_name=item["owners"][0]["displayName"],
        )

        return doc

    def _ignore_file_check(self, *args, **kwargs):
        """
        Return True if this file should be ignored when assembling the remote list of files.
        Subclasses can override this method to filter files by name.
        They should check the result of super()._ignore_file_check(...) first.

        :param fname: name of the file
        :returns bool: return True if this file should be ignored when compiling the list of remote
        """
        # Eventually this will check if a GDriveDocxDoctype is activated
        # If so, ignore docx files to avoid duplicate search index entries
        return False


class GDriveDocxDoctype(GDriveFileDoctype):
    doctype = "gdrive_docx"
    """
    Defines a Google Drive docx filetype.
    This indexes the name and contents of docx files, using
    pandoc to convert the docx file to text that is indexed.
    """
    schema = dict(
        **GDriveFileDoctype.schema,
        content=fields.TEXT(stored=True, analyzer=get_stemming_analyzer()),
    )

    @classmethod
    def get_jinja_template(cls) -> str:
        """
        Return a string containing Jinja HTML template for rendering
        search results of this doctype. Must match schema.
        """
        template = """
                <div class="url">
                    <a class="result-title" href="{{e.url}}">{{e.title}}</a>
                    <br />
                    <span class="badge kind-badge">Google Document</span>
                    <br />
                    <b>Owner:</b> {{e.owner_name}} &lt;{{e.owner_email}}&gt;
                    <br/>
                    <b>Repository:</b> <a href="{{e.repo_url}}">{{e.repo_name}}</a>
                    {% if e.mimetype %}
                        <br />
                        <b>Document Type</b>: {{e.mimetype}}
                    {% endif %}
                    {% if e.created_time %}
                        <br/>
                        <b>Created:</b> {{e.created_time}}
                    {% endif %}
                    {% if e.modified_time %}
                        <br/>
                        <b>Modified:</b> {{e.modified_time}}
                    {% endif %}
                </div>
                <div class="markdown-body">
                    <p>(A preview of this document is not available.)</p>
                </div>
        """
        return template

    def _ignore_file_check(self, fname, mimetype):

        # Include files with .docx or .doc extension
        fprefix, fext = os.path.splitext(fname)
        if fext in [".docx", ".doc"]:
            return False

        # Include files with mimetype
        docx_mimetypes = ["application/vnd.google-apps.document"]
        if mimetype in docx_mimetypes:
            return False

        # Ignore everything else
        return True

    def get_by_id(self, doc_id):
        """
        Retrieve a remote docx document given its id.
        Use markdown to extract the text contents of the doc.
        Assemble and return an item to the search index
        matching the search index schema.
        """
        # uses get method: https://developers.google.com/drive/api/v3/reference/files/get
        item = self.drive.files().get(doc_id)
        content = self._extract_docx_content(item)
        doc = super().get_by_id(doc_id)
        doc["content"] = content

    def _extract_docx_content(self, item):
        content = ""
        mimetype = re.split(r"[/\.]", item["mimeType"])[-1]
        mimemap = {"document": "docx"}
        if mimetype not in mimemap.keys():
            # Not a document - just a file
            return content

        msg = 'Indexing content of Google Drive document "%s" of type "%s"' % (
            item["name"],
            mimetype,
        )
        logger.info(msg)

        msg = " > Extracting content"
        logger.info(msg)

        # Create a URL and a destination filename
        file_ext = mimemap[mimetype]
        file_url = "https://docs.google.com/document/d/%s/export?format=%s" % (item["id"], file_ext)

        # This re could probablybe improved
        name = re.sub("/", "_", item["name"])

        # Now make the pandoc input/output filenames
        out_ext = "txt"
        pandoc_fmt = "plain"
        if name.endswith(file_ext):
            infile_name = name
            outfile_name = re.sub(file_ext, out_ext, infile_name)
        else:
            infile_name = name + "." + file_ext
            outfile_name = name + "." + out_ext

        # Get the temporary directory, $CENTILLION_ROOT/tmp,
        # from the config file (so everyone uses the same one)
        temp_dir = Config.get_centillion_tmpdir()

        # Assemble input/output file paths
        fullpath_input = os.path.join(temp_dir, infile_name)
        fullpath_output = os.path.join(temp_dir, outfile_name)

        # Use requests.get to download url to file
        r = requests.get(file_url, allow_redirects=True)
        with open(fullpath_input, "wb") as f:
            f.write(r.content)

        # Try to convert docx file to plain text
        try:
            output = pypandoc.convert_file(
                fullpath_input, pandoc_fmt, format="docx", outputfile=fullpath_output
            )
            assert output == ""
        except RuntimeError:
            err = ' > XXXXXX Failed to index Google Drive document "%s"' % (item["name"])
            logger.error(err)

        # If export was successful, read contents of markdown
        # into the content variable.
        if os.path.isfile(fullpath_output):
            # Export was successful
            with codecs.open(fullpath_output, encoding="utf-8") as f:
                content = f.read()

        # No matter what happens, clean up.
        msg = ' > Cleaning up "%s"' % (item["name"])
        logger.info(msg)

        clean_in_cmd = ["rm", "-fr", fullpath_input]
        clean_out_cmd = ["rm", "-fr", fullpath_output]

        logger.info(" > " + " ".join(clean_in_cmd))
        subprocess.call(clean_in_cmd)

        logger.info(" > " + " ".join(clean_out_cmd))
        subprocess.call(clean_out_cmd)

        return content
