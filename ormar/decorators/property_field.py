import inspect
from collections.abc import Callable
from typing import Union

from ormar.exceptions import ModelDefinitionError


def property_field(func: Callable) -> Union[property, Callable]:
    if isinstance(func, property):  # pragma: no cover
        func.fget.__property_field__ = True
    else:
        arguments = list(inspect.signature(func).parameters.keys())
        if len(arguments) > 1 or arguments[0] != "self":
            raise ModelDefinitionError(
                "property_field decorator can be used "
                "only on methods with no arguments"
            )
        func.__dict__["__property_field__"] = True
    return func
