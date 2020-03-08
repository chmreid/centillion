import logging


logger = logging.getLogger(__name__)


class DoctypeRegistry(type):
    """
    Metaclass that forces all classes using it to
    register their subclass types in a single
    global registry.
    """
    REGISTRY = {}
    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)
        try:
            new_name = new_cls.doctype
        except AttributeError:
            new_name = new_cls.__name__
            logger.warn(f"Class attribute doctype not defined for {new_name}")
        cls.REGISTRY[new_name] = new_cls

    @classmethod
    def get_registry(cls):
        return dict(cls.REGISTRY)
