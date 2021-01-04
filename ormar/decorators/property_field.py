import inspect
from collections.abc import Callable
from typing import Union

from ormar.exceptions import ModelDefinitionError


def property_field(func: Callable) -> Union[property, Callable]:
    """
    Decorator to set a property like function on Model to be exposed
    as field in dict() and fastapi response.
    Although you can decorate a @property field like this and this will work,
    mypy validation will complain about this.
    Note that "fields" exposed like this do not go through validation.

    :raises ModelDefinitionError: if method has any other argument than self.
    :param func: decorated function to be exposed
    :type func: Callable
    :return: decorated function passed in func param, with set __property_field__ = True
    :rtype: Union[property, Callable]
    """
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
