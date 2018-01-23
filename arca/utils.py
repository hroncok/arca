import importlib
import logging
from typing import Any, Dict, Optional, Callable

from .exceptions import ArcaMisconfigured


NOT_SET = object()
logger = logging.getLogger("arca")
logger.setLevel(logging.DEBUG)


def load_class(location: str) -> type:
    module_name = ".".join(location.split(".")[:-1])
    class_name = location.split(".")[-1]

    try:
        imported_module = importlib.import_module(module_name)
        return getattr(imported_module, class_name)
    except ModuleNotFoundError:
        raise ArcaMisconfigured(f"{module_name} does not exist.")
    except AttributeError:
        raise ArcaMisconfigured(f"{module_name} does not have a {class_name} class")


class LazySettingProperty:
    def __init__(self, *, key, default=NOT_SET, convert: Callable=None) -> None:
        self.key = key
        self.default = default
        self.convert = convert

    def __set_name__(self, cls, name):
        self.name = name

    def __get__(self, instance, cls):
        if instance is None or (hasattr(instance, "_arca") and instance._arca is None):
            return self
        result = instance.get_setting(self.key, self.default)

        if self.convert is not None:
            result = self.convert(result)

        setattr(instance, self.name, result)
        return result


class Settings:

    PREFIX = "ARCA"

    def __init__(self, data: Optional[Dict[str, Any]]=None) -> None:
        self.data = data or {}

    def get(self, *options: str, default: Any=NOT_SET) -> Any:
        if not len(options):
            raise ValueError("At least one key must be provided.")

        for option in options:
            key = f"{self.PREFIX}_{option.upper()}"
            if key in self:
                return self[key]

        if default is NOT_SET:
            raise KeyError("None of the following key is present in settings and no default is set: {}".format(
                ", ".join(options)
            ))

        return default

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data
