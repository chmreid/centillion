import os
import typing
from enum import Enum, auto


class FooConfig(Enum):
    FOO = auto()
    BAR = auto()


class Config:
    _FOO_VAR: typing.Optional[str] = None

    @staticmethod
    def _get_required_envvar(envvar: str) -> str:
        if envvar not in os.environ:
            raise Exception("Please set the {} environment variable".format(envvar))
        return os.environ[envvar]
    
    @staticmethod
    def get_foo_var() -> str:
        val = Config._get_required_envvar("FOO_VAR")
        Config._FOO_VAR = val
        return Config._FOO_VAR
