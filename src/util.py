import datetime
import os


class dotdict(dict):
    """
    Dictionary that makes members accessible using dot.notation.
    Also see https://stackoverflow.com/q/2352181/463213
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super().__delitem__(key)
        del self.__dict__[key]


# Having dot.notation access is useful for this class
class SearchResult(dotdict):
    pass


def clean_timestamp(dt):
    return dt.replace(microsecond=0).isoformat()


def search_results_timestamps_datetime_to_str(result):
    """Parse and process datetime objects into strings"""
    result.created_time = datetime.datetime.strftime(result.created_time, "%Y-%m-%d %I:%M %p")
    result.modified_time = datetime.datetime.strftime(result.modified_time, "%Y-%m-%d %I:%M %p")
    result.indexed_time = datetime.datetime.strftime(result.indexed_time, "%Y-%m-%d %I:%M %p")


def is_url_whoosh(u: str) -> bool:
    """
    Check if a string is a URL.

    :param u: string to check
    :returns bool: True if string is a url.
    """
    if "..." in u:
        # special case of whoosh messing up urls
        return False
    if "<b" in u or "&lt;" in u:
        # special case of whoosh highlighting a word in a link
        return False
    if u[-1] == "-":
        # parsing error
        return False
    if u[0:2] == "ht" or u[0:2] == "ft" or u[0:2] == "//":
        return True
    return False


def is_absolute_path(path):
    if os.path.abspath(path) == path:
        return True
    return False
