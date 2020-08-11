from typing import Any, TYPE_CHECKING, Type

from orm import ModelDefinitionError

if TYPE_CHECKING:  # pragma no cover
    from orm.fields import BaseField


class RequiredParams:
    def __init__(self, *args: str) -> None:
        self._required = list(args)

    def __call__(self, model_field_class: Type["BaseField"]) -> Type["BaseField"]:
        old_init = model_field_class.__init__
        model_field_class._old_init = old_init

        def __init__(instance: "BaseField", *args: Any, **kwargs: Any) -> None:
            super(instance.__class__, instance).__init__(*args, **kwargs)
            for arg in self._required:
                if arg not in kwargs:
                    raise ModelDefinitionError(
                        f"{instance.__class__.__name__} field requires parameter: {arg}"
                    )
                setattr(instance, arg, kwargs.pop(arg))

        model_field_class.__init__ = __init__
        return model_field_class
