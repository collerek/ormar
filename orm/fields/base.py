from typing import Type, Any, Dict, Optional, List

import sqlalchemy

from orm import ModelDefinitionError


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


class BaseField:
    __type__ = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        name = kwargs.pop("name", None)
        args = list(args)
        if args:
            if isinstance(args[0], str):
                if name is not None:
                    raise ModelDefinitionError(
                        "Column name cannot be passed positionally and as a keyword."
                    )
                name = args.pop(0)

        self.name = name
        self._populate_from_kwargs(kwargs)

    def _populate_from_kwargs(self, kwargs: Dict) -> None:
        self.primary_key = kwargs.pop("primary_key", False)
        self.autoincrement = kwargs.pop(
            "autoincrement", self.primary_key and self.__type__ == int
        )

        self.nullable = kwargs.pop("nullable", not self.primary_key)
        self.default = kwargs.pop("default", None)
        self.server_default = kwargs.pop("server_default", None)

        self.index = kwargs.pop("index", None)
        self.unique = kwargs.pop("unique", None)

        self.pydantic_only = kwargs.pop("pydantic_only", False)
        if self.pydantic_only and self.primary_key:
            raise ModelDefinitionError("Primary key column cannot be pydantic only.")

    @property
    def is_required(self) -> bool:
        return (
            not self.nullable and not self.has_default and not self.is_auto_primary_key
        )

    @property
    def default_value(self) -> Any:
        default = self.default if self.default is not None else self.server_default
        return default() if callable(default) else default

    @property
    def has_default(self) -> bool:
        return self.default is not None or self.server_default is not None

    @property
    def is_auto_primary_key(self) -> bool:
        if self.primary_key:
            return self.autoincrement
        return False

    def get_column(self, name: str = None) -> sqlalchemy.Column:
        self.name = self.name or name
        constraints = self.get_constraints()
        return sqlalchemy.Column(
            self.name,
            self.get_column_type(),
            *constraints,
            primary_key=self.primary_key,
            autoincrement=self.autoincrement,
            nullable=self.nullable,
            index=self.index,
            unique=self.unique,
            default=self.default,
            server_default=self.server_default,
        )

    def get_column_type(self) -> sqlalchemy.types.TypeEngine:
        raise NotImplementedError()  # pragma: no cover

    def get_constraints(self) -> Optional[List]:
        return []

    def expand_relationship(self, value: Any, child: "Model") -> Any:
        return value
