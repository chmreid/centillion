import typing
from centillion.doctypes.doctype import Doctype


######################
# Test Doctype classes
######################


class PlainDoctype(Doctype):
    doctype = "plain"
    name: typing.Optional[str] = None
    schema: Doctype.common_schema

    def __init__(self, *args, **kwargs):
        self.name = args[0]
