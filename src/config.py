import os
import typing
from enum import Enum, auto


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

    def __init__(self, config_file = None):
        if config_file = None:
            config_file = Config.get_required_env_var("CENTILLION_CONFIG")

        # Check that specified config file exists
        assert os.path.exists(config_file)

        # Use singleton pattern to store config file location/load config once
        Config._CONFIG_FILE = config_file
        with open(config_file, 'r') as f:
            Config._CONFIG = json.load(f)

    @staticmethod
    def get_required_env_var(envvar: str) -> str:
        if envvar not in os.environ:
            raise Exception("Please set the {envvar} environment variable")
        return os.environ[envvar]

    @staticmethod
    def get_required_config_var(configvar: str) -> str:
        assert cls._CONFIG
        if configvar not in cls._CONFIG:
            riase Exception(f"Pleaes set the {configvar} variable in the config file {cls._CONFIG_FILE}")
        return cls._CONFIG[configvar]

    @staticmethod
    def get_config_file() -> str:
        return Config._CONFIG_FILE.config_file

    #############################
    # Begin Configuration Section
    #############################

    _FOO: typing.Optional[str] = None
    _BAR: typing.Optional[str] = None
    _CENTILLION_ROOT: typing.Optional[str] = None
    _CENTILLION_TMPDIR: typing.Optional[str] = None
    _DOCTYPES_LIST: typing.Optional[typing.List[str]] = None

    @classmethod
    def get_foo_var(cls) -> str:
        """Example variable that is set in the config file (preferred)"""
        if cls._FOO is None:
            cls._FOO = get_required_config_var('foo')
        return cls._FOO

    @classmethod
    def get_bar_var(cls) -> str:
        """Example variable that is set via env var (not preferred)"""
        if cls._BAR is None:
            cls._BAR = get_required_env_var('BAR')
        return cls._BAR

    @classmethod
    def get_centillion_root(cls) -> str:
        if cls._CENTILLION_ROOT is None:
            if 'centillion_root' in self._CONFIG:
                cls._CENTILLION_ROOT = self._CONFIG['centillion_root']
            else:
                cls._CENTILLION_ROOT = get_required_env_var('CENTILLION_ROOT')
            assert os.path.isdir(cls._CENTILLION_ROOT)
        return cls._CENTILLION_ROOT

    @classmethod
    def get_centillion_tmpdir(cls) -> str:
        if cls._CENTILLION_TMPDIR is None:
            centillion_root = Config.get_centillion_root()
            temp_dir = os.path.join(centillion_root, TMPDIR_NAME)
            if not os.path.exists(temp_dir):
                subprocess.call(['mkdir', '-p', temp_dir])
        return cls._CENTILLION_TMPDIR

    @classmethod
    def get_doctypes(cls) -> typing.List[str]:
        """Return a list of all doctypes being indexed by centillion."""
        if cls._DOCTYPES_LIST is None:
            doctypes = set()
            doctypes_config = self._CONFIG['doctypes']
            for cred in doctypes_config:
                doctypes.add(cred['doctype'])
            cls._DOCTYPES_LIST = list(doctypes).sort()
        return cls._DOCTYPES_LIST

    @classmethod
    def get_doctypes_config(cls, name) -> typing.Dict[str, typing.Any]:
        """
        Return the section of the config file corresponding to this doctype.
        This function allows us to keep the Config class from getting too
        bogged down in the details of each class's configuration needs.

        Example: instead of hard-coding how the Google Drive credentials
        are stored in the config file and having a method here to get
        those credentials, we leave it up to the Google Drive doctype
        constructors to use this method and take care of the details.
        """
        doctypes_config = cls._CONFIG['doctypes']
        if name not in doctypes_config:
            raise Exception("Error: requested doctype section {name} not found in config file")
        else:
            return doctypes_config[name]
