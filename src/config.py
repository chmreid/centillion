import os
import typing
from enum import Enum, auto


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
        if not Config._CONFIG:
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
