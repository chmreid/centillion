import os
import sys
import shutil
import json
import logging
import tempfile
from io import StringIO

from centillion.config import Config


logger = logging.getLogger(__name__)


#########################
# Context Manager classes
#########################


class TempCentillionConfig(object):
    """
    Temporarily patch the Config class to use the config
    dictionary specified in the constructor.
    Example:

        sample_config = { ... }
        with TempCentillionConfig(sample_config) as config_file:
            print(f"Now the config file is set to {config_file}")

    By default, the centillion_root variable is set to a
    temporary directory that is created/destroyed with this
    context manager. This can be overridden with the
    centillion_root argument:

        sample_config = { ... }
        with TempCentillionConfig(sample_config, centillion_root="/tmp/tmp613o6l9na3ihffan")
    """

    def __init__(self, config_dict, *args, **kwargs):
        """This is the step that's run when object constructed"""
        super().__init__()
        # This is the temp configuration the user specified
        self.config_dict = config_dict
        # Make a temp dir for our temp config file
        self.temp_dir = tempfile.mkdtemp()
        # Make a temp config file
        _, self.temp_json = tempfile.mkstemp(suffix=".json", dir=self.temp_dir)
        # Check for centillion as follows:
        # - centillion_root kwarg (top priority)
        # - centillion_root in config file (passed along)
        # - centillion_root default value (temp dir)
        rt = 'centillion_root'
        if rt not in kwargs.keys():
            if rt not in config_dict.keys():
                self.config_dict[rt] = self.temp_dir
            else:
                self.config_dict[rt] = config_dict[rt]
        else:
            self.config_dict[rt] = kwargs[rt]

    def __enter__(self, *args, **kwargs):
        """This is what's returned to the "as X" portion of the context manager"""
        self._write_config(self.temp_json, json.dumps(self.config_dict))
        # Save the old config file location
        self._old_config_file = Config.get_config_file()
        # Re-init Config with new config file
        Config(self.temp_json)
        return self.temp_json

    def __exit__(self, *args, **kwargs):
        """
        Close the context and clean up; the *args are needed in case there is
        an exception (we don't deal with those here)
        """
        # Delete temp file
        os.unlink(self.temp_json)
        # Delete temp dir
        shutil.rmtree(self.temp_dir)
        # Reset all config variables
        Config.reset()

    def _write_config(self, target: str, contents: str):
        """Utility method: write string contents to config file"""
        with open(target, "w") as f:
            f.write(contents)


class CaptureStdout(list):
    """
    Utility object using a context manager to capture stdout for a given block
    of Python code. Subclass of list so that you can access stdout lines like a
    list.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def __enter__(self, *args, **kwargs):
        """
        The function called when we open the context, this function swaps out
        sys.stdout with a string buffer and saves the sys.stdout reference.
        """
        # Save existing stdout object so we can restore it when we're done
        self._stdout = sys.stdout
        # Swap out stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Close the context and clean up; the *args are needed in case there is
        an exception (we don't deal with those here)
        """
        # This class extends the list class, so call self.extend to add a list
        # to the end of self. This is to add all of the new lines from the
        # StringIO object.
        self.extend(self._stringio.getvalue().splitlines())

        # Clean up (if this is missing, the garbage collector will eventually
        # take care of this...)
        del self._stringio

        # Clean up by setting sys.stdout back to what it was before we opened
        # up this context
        sys.stdout = self._stdout
