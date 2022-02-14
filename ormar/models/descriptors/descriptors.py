import base64
import collections
from typing import Any, TYPE_CHECKING, Tuple, Type, Union, cast

import ormar

from ormar.fields.parsers import encode_json

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


class PydanticDescriptor:
    """
    Pydantic descriptor simply delegates everything to pydantic model
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        value = instance.__dict__.get(self.name, None)
        return value

    def __set__(self, instance: "Model", value: Any) -> None:
        instance._internal_set(self.name, value)
        instance.set_save_status(False)


class JsonDescriptor:
    """
    Json descriptor dumps/loads strings to actual data on write/read
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        value = instance.__dict__.get(self.name, None)
        return value

    def __set__(self, instance: "Model", value: Any) -> None:
        value = encode_json(value)
        instance._internal_set(self.name, value)
        instance.set_save_status(False)


class BytesDescriptor:
    """
    Bytes descriptor converts strings to bytes on write and converts bytes to str
    if represent_as_base64_str flag is set, so the value can be dumped to json
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        value = instance.__dict__.get(self.name, None)
        field = instance.Meta.model_fields[self.name]
        if (
            value is not None
            and field.represent_as_base64_str
            and not isinstance(value, str)
        ):
            value = base64.b64encode(value).decode()
        return value

    def __set__(self, instance: "Model", value: Any) -> None:
        field = instance.Meta.model_fields[self.name]
        if isinstance(value, str):
            if field.represent_as_base64_str:
                value = base64.b64decode(value)
            else:
                value = value.encode("utf-8")
        instance._internal_set(self.name, value)
        instance.set_save_status(False)


class PkDescriptor:
    """
    As of now it's basically a copy of PydanticDescriptor but that will
    change in the future with multi column primary keys
    """

    def __init__(self, name: Union[str, Tuple[str]]) -> None:
        self.name = name
        self.is_compound = isinstance(name, tuple)

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        if self.is_compound:
            pk_dict = dict()
            for name in self.name:
                target_field_name = owner.get_column_name_from_alias(name)
                target_value = instance.__dict__.get(target_field_name, None)
                if isinstance(target_value, ormar.Model):
                    target_value = target_value.pk
                if isinstance(target_value, dict):
                    target_field = owner.Meta.model_fields[target_field_name]
                    names = target_field.names
                    for target_name, own_name in names.items():
                        if own_name not in pk_dict:
                            pk_dict[own_name] = target_value.get(target_name)
                else:
                    pk_dict[name] = target_value
            return pk_dict
        value = instance.__dict__.get(cast(str, self.name), None)
        return value

    def __set__(self, instance: "Model", value: Any) -> None:
        if self.is_compound:
            if isinstance(value, collections.abc.Mapping):
                for key, value_ in value.items():
                    if key in instance.extract_related_names():
                        setattr(instance, key, value_)
                    else:
                        instance._internal_set(key, value_)
            else:
                raise ormar.ModelDefinitionError(
                    "Compound primary key can be set only with dictionary"
                )
        else:
            instance._internal_set(cast(str, self.name), value)
        instance.set_save_status(False)


class RelationDescriptor:
    """
    Relation descriptor expands the relation to initialize the related model
    before setting it to __dict__. Note that expanding also registers the
    related model in RelationManager.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        if self.name in instance._orm:
            return instance._orm.get(self.name)  # type: ignore
        return None  # pragma no cover

    def __set__(self, instance: "Model", value: Any) -> None:
        model = instance.Meta.model_fields[self.name].expand_relationship(
            value=value, child=instance
        )
        if isinstance(instance.__dict__.get(self.name), list):
            # virtual foreign key or many to many
            # TODO: Fix double items in dict, no effect on real action just ugly repr
            instance.__dict__[self.name].append(model)
        else:
            # foreign key relation
            instance.__dict__[self.name] = model
            instance.set_save_status(False)


class PropertyDescriptor:
    """
    Property descriptor handles methods decorated with @property_field decorator.
    They are read only.
    """

    def __init__(self, name: str, function: Any) -> None:
        self.name = name
        self.function = function

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        if instance is None:
            return self
        if instance is not None and self.function is not None:
            bound = self.function.__get__(instance, instance.__class__)
            return bound() if callable(bound) else bound

    def __set__(self, instance: "Model", value: Any) -> None:  # pragma: no cover
        # kept here so it's a data-descriptor and precedes __dict__ lookup
        pass


class DeniedDescriptor:
    """
    Multi column foreign key descriptor for fields that are part of the fk
    """

    def __init__(self, name: str, relation_name: str) -> None:
        self.name = name
        self.relation_name = relation_name

    def __get__(self, instance: "Model", owner: Type["Model"]) -> Any:
        if instance is None:
            return self
        raise ormar.ModelError(
            f"You cannot access field {self.name} directly. "
            f"Use {self.relation_name} relation to get the field"
        )

    def __set__(self, instance: "Model", value: Any) -> None:
        raise ormar.ModelError(
            f"You cannot set field {self.name} directly. "
            f"Use {self.relation_name} relation to set the field"
        )
