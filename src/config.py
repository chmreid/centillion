import os
import json
import typing
import subprocess
from .error import CentillionConfigException


TMPDIR_NAME = 'tmp'


class Config(object):
    """
    Singleton class to allow uniform access to centillion configuration.
    Uses a singleton pattern to store the config file location once.

    Example:

        >>> c = Config('/path/to/my/config.json')
        >>> print(Config.get_config_file())
        /path/to/my/config.json
    """

    #########################
    # Begin Singleton Section
    #########################

    _CONFIG_FILE: typing.Optional[str] = None
    _CONFIG: typing.Optional[dict] = None

    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Config.get_required_env_var("CENTILLION_CONFIG")

        # Check that specified config file exists
        config_file = os.path.abspath(config_file)
        if not os.path.exists(config_file):
            raise CentillionConfigException(f"Error: Path does not exist: {config_file}")

        # Use singleton pattern to store config file location/load config once
        Config._CONFIG_FILE = config_file
        with open(config_file, 'r') as f:
            Config._CONFIG = json.load(f)

    @staticmethod
    def get_required_env_var(envvar: str) -> str:
        if envvar not in os.environ:
            raise CentillionConfigException(f"Please set the {envvar} environment variable")
        return os.environ[envvar]

    @staticmethod
    def get_required_config_var(configvar: str) -> str:
        if not Config._CONFIG:
            err = f"Configuration is missing, using file {Config._CONFIG_FILE}"
            raise CentillionConfigException(err)
        if configvar not in Config._CONFIG:
            err = f"Please set the {configvar} variable in the config file {Config._CONFIG_FILE}"
            raise CentillionConfigException(err)
        return Config._CONFIG[configvar]

    @staticmethod
    def get_config_file() -> str:
        return Config._CONFIG_FILE

    #############################
    # Begin Configuration Section
    #############################

    '''
    _FOO: typing.Optional[str] = None
    _BAR: typing.Optional[str] = None

    @classmethod
    def get_foo_var(cls) -> str:
        """Example variable that is set in the config file (preferred)"""
        if cls._FOO is None:
            cls._FOO = Config.get_required_config_var('foo')
        return cls._FOO

    @classmethod
    def get_bar_var(cls) -> str:
        """Example variable that is set via env var (not preferred)"""
        if cls._BAR is None:
            cls._BAR = Config.get_required_env_var('BAR')
        return cls._BAR
    '''

    _CENTILLION_ROOT: typing.Optional[str] = None
    _CENTILLION_TMPDIR: typing.Optional[str] = None
    _DOCTYPES_LIST: typing.Optional[typing.List[str]] = None
    _DOCTYPES_NAMES_MAP: typing.Optional[typing.Dict[str, typing.List[str]]] = None

    @classmethod
    def get_centillion_root(cls) -> str:
        if cls._CENTILLION_ROOT is None:
            if 'centillion_root' in cls._CONFIG:
                cls._CENTILLION_ROOT = cls._CONFIG['centillion_root']
            else:
                cls._CENTILLION_ROOT = Config.get_required_env_var('CENTILLION_ROOT')
            if not os.path.isdir(cls._CENTILLION_ROOT):
                raise CentillionConfigException(f"Error: Path {cls._CENTILLION_ROOT} is not a directory")
        return cls._CENTILLION_ROOT

    @classmethod
    def get_centillion_tmpdir(cls) -> str:
        if cls._CENTILLION_TMPDIR is None:
            centillion_root = Config.get_centillion_root()
            tmp_dir = os.path.join(centillion_root, TMPDIR_NAME)
            if not os.path.exists(tmp_dir):
                subprocess.call(['mkdir', '-p', tmp_dir])
            cls._CENTILLION_TMPDIR = tmp_dir
        return cls._CENTILLION_TMPDIR

    @classmethod
    def get_doctypes(cls) -> typing.List[str]:
        """Return a list of all doctypes being indexed by centillion."""
        if cls._DOCTYPES_LIST is None:
            doctypes = set()
            for cred in cls._CONFIG['doctypes']:
                doctypes.add(cred['doctype'])
            cls._DOCTYPES_LIST = sorted(list(doctypes))
        return cls._DOCTYPES_LIST

    @classmethod
    def get_doctype(cls, name) -> str:
        """
        Return the "doctype" key of the credentials with the given name
        """
        doctype_config = cls.get_doctype_config(name)
        return doctype_config['doctype']

    @classmethod
    def get_doctype_config(cls, name) -> typing.Dict[str, typing.Any]:
        """
        Return the section of the config file corresponding to this doctype.
        This function allows us to keep the Config class from getting too
        bogged down in the details of each class's configuration needs.

        Example: instead of hard-coding how the Google Drive credentials
        are stored in the config file and having a method here to get
        those credentials, we leave it up to the Google Drive doctype
        constructors to use this method and take care of the details.
        """
        all_doctypes_config = cls._CONFIG['doctypes']

        for creds in all_doctypes_config:
            if creds['name'] == name:
                return creds

        # We didn't find the credentials we were looking for, assemble a helpful error message
        creds_list = ", ".join([creds['name'] for creds in all_doctypes_config])
        err = f"Error: Requested Doctype item named {name} not found in config file.\n"
        err += f"Found credentials named: {creds_list}"
        raise CentillionConfigException(err)

    @classmethod
    def get_doctypes_names_map(cls) -> typing.Dict[str, typing.List[str]]:
        """
        Return a map of doctype labels (strings identifying doctype)
        to the name of the corresponding credentials in the config file.
        Each doctype can have multiple credentials, so return type is
        a map of string (doctype) to list of strings (names).

        :returns: map of doctype to a list of credential names
        """
        if cls._DOCTYPES_NAMES_MAP is None:
            doctypes_names_map: typing.Dict = dict()
            doctypes_config = cls._CONFIG['doctypes']
            for cred in doctypes_config:
                name = cred['name']
                doctype = cred['doctype']
                if doctype in doctypes_names_map:
                    doctypes_names_map[doctype] = doctypes_names_map[doctype].append(name)
                else:
                    doctypes_names_map[doctype] = [name]
            cls._DOCTYPES_NAMES_MAP = doctypes_names_map
        return cls._DOCTYPES_NAMES_MAP
