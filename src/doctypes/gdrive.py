"""Defines several Google Drive doctypes"""
import os
import subprocess
import logging
import datetime
import pypandoc
from dateutil.parser import parse
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


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

    Then token_path above should be set to the path of credentials.json
    """
    SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
    store = file.Storage(token_path)
    creds = store.get()
    if not creds or creds.invalid:
        raise Exception("Error: invalid or missing Google Drive API credentials")
    service = build('drive', 'v3', http=creds.authorize(Http()))
    return service.files()


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
    drive = None

    def __init__(self, *args, **kwargs):
        """
        Constructor is only passed the name of the credentials.
        Constructor uses name to get GDrive credentials.
        """
        self.name = args[0]
        config = Config.get_doctypes_config(self.name)
        self.token_path = config['token_path']
        self.validate_credentials(self.token_path)

    def validate_credentials(self, token_path):
        if not os.path.exists(token_path):
            raise Exception("Error: Google Drive token path does not exist: {token_path}")
        if self.drive == None:
            self.drive = get_gdrive_service(token_path)


class GDriveFileDoctype(GDriveBaseDoctype):
    doctype = "gdrive_file"
    """
    Defines a Google Drive file filetype.
    This indexes the name/metadata of all files in a given
    Google Drive folder/location.
    """
    schema = dict(
        file_name = fields.TEXT(stored=True, field_boost=100.0),
        file_url = fields.ID(stored=True),
        mimetype = fields.TEXT(stored=True),
        owner_email = fields.TEXT(stored=True),
        owner_name = fields.TEXT(stored=True)
    )

    def get_remote_list(self) -> typing.List[typing.Tuple[datetime.datetime, str]]:
        """
        Compile a list of document IDs for documents that can be indexed
        at the remote, and their last modified date.

        Google Drive uses GDrive ID for the search index ID.

        :returns: list of (last_modified_date, gdrive id) tuples
                  (types are datetime.datetime and str)
        """
        name = self.name
        drive = self.drive

        # Return value: list of (last_modified_date, gdrive_id) tuples
        remote_list = []

        # To iterate over all files, use the list() function of drive
        nextPageToken = None  # This is the trick to get this to work

        # Use the pager to return all the things
        while True:
            ps = 100
            results = drive.list(
                    pageSize=ps,
                    pageToken=nextPageToken,
                    fields = "nextPageToken, files(id, kind, createdTime, modifiedTime, mimeType, name, owners, webViewLink)",
                    spaces="drive"
            ).execute()

            nextPageToken = results.get("nextPageToken")
            files = results.get("files",[])
            for f in files:
                fid = f['id']
                fname = f['name']
                ignore_file = self._ignore_file_check(fname)
                if not ignore_file:
                    key = fid
                    date = dateutil.parser.parse(item['modifiedTime'])
                    remote_list.append((date, key))

        return remote_list

    def get_by_id(self, doc_id):
        """
        Retrieve a remote document given its id, and return
        an item to the search index matching the index schema.
        """
        # uses get method: https://developers.google.com/drive/api/v3/reference/files/get
        item = driveService.files().get(doc_id)

        doc = dict(
            id = doc_id,
            fingerprint = item['md5Checksum'],
            kind = self.doctype,
            created_time = dateutil.parser.parse(item['createdTime']),
            modified_time = dateutil.parser.parse(item['modifiedTime']),
            indexed_time = datetime.datetime.now(),
            name = item['name'],
            file_name = item['name'],
            file_url = item['webViewLink'],
            mimetype = item['mimeType'],
            owner_email = item['owners'][0]['emailAddress'],
            owner_name = item['owners'][0]['displayName']
        )

        return doc

    def _ignore_file_check(self, fname):
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
        content = fields.TEXT(stored=True)
    )

    def _ignore_file_check(self, fname):
        fprefix, fext = os.path.splitext(fname)
        if fext not in ['.docx', '.doc']:
            return True
        return False

    def get_by_id(self, doc_id):
        """
        Retrieve a remote docx document given its id.
        Use markdown to extract the text contents of the doc.
        Assemble and return an item to the search index 
        matching the search index schema.
        """
        # uses get method: https://developers.google.com/drive/api/v3/reference/files/get
        item = driveService.files().get(doc_id)
        content = self._extract_docx_content(item)
        doc = super().get_by_id(doc_id)
        doc['content'] = content

    def _extract_docx_content(self, item):
        content = ""
        mimetype = re.split('[/\.]',item['mimeType'])[-1]
        mimemap = {
                'document' : 'docx',
        }
        if mimetype not in mimemap.keys():
            # Not a document - just a file
            return content

        msg = f"Indexing content of Google Drive document \"{item['name'}\" of type \"{mimetype}\""
        logger.info(msg)

        msg = " > Extracting content"
        logger.info(msg)

        # Create a URL and a destination filename
        file_ext = mimemap[mimetype]
        file_url = "https://docs.google.com/document/d/%s/export?format=%s"%(item['id'], file_ext)

        # This re could probablybe improved
        name = re.sub('/','_',item['name'])

        # Now make the pandoc input/output filenames
        out_ext = 'txt'
        pandoc_fmt = 'plain'
        if name.endswith(file_ext):
            infile_name = name
            outfile_name = re.sub(file_ext, out_ext, infile_name)
        else:
            infile_name  = name+'.'+file_ext
            outfile_name = name+'.'+out_ext

        # Get the temporary directory, $CENTILLION_ROOT/tmp,
        # from the config file (so everyone uses the same one)
        temp_dir = Config.get_centillion_tmpdir()

        # Assemble input/output file paths
        fullpath_input = os.path.join(temp_dir,infile_name)
        fullpath_output = os.path.join(temp_dir,outfile_name)

        # Use requests.get to download url to file
        r = requests.get(file_url, allow_redirects=True)
        with open(fullpath_input, 'wb') as f:
            f.write(r.content)

        # Try to convert docx file to plain text
        try:
            output = pypandoc.convert_file(fullpath_input,
                                           pandoc_fmt,
                                           format='docx',
                                           outputfile=fullpath_output
            )
            assert output == ""
        except RuntimeError:
            err = " > XXXXXX Failed to index Google Drive document \"%s\""%(item['name'])
            logger.error(err)

        # If export was successful, read contents of markdown
        # into the content variable.
        if os.path.isfile(fullpath_output):
            # Export was successful
            with codecs.open(fullpath_output, encoding='utf-8') as f:
                content = f.read()

        # No matter what happens, clean up.
        msg = f" > Cleaning up \"{item['name']}\""
        logger.info(msg)

        clean_in_cmd = ['rm','-fr',fullpath_input]
        clean_out_cmd = ['rm','-fr',fullpath_output]

        logger.info(" > " + " ".join(clean_in_cmd))
        subprocess.call(clean_in_cmd)

        logger.info(" > " + " ".joout(clean_out_cmd))
        subprocess.call(clean_out_cmd)

        return content
