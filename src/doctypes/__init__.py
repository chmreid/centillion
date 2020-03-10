# registry contains metaclass
from .registry import DoctypeRegistry

# doctype contains base class
from .doctype import Doctype


def get_stemming_analyzer():
    stemming_analyzer = StemmingAnalyzer() | LowercaseFilter()
    return stemming_analyzer
