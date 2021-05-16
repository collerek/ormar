import pydantic

from ormar.models.helpers.validation import validate_choices


class PydanticDescriptor:

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        value = object.__getattribute__(instance, "__dict__").get(self.name, None)
        value = object.__getattribute__(instance, "_convert_json")(self.name, value,
                                                                   "loads")
        value = object.__getattribute__(instance, "_convert_bytes")(self.name, value,
                                                                    "read")
        return value

    def __set__(self, instance, value):
        if self.name in object.__getattribute__(instance, "_choices_fields"):
            validate_choices(field=instance.Meta.model_fields[self.name], value=value)
        value = object.__getattribute__(instance, '_convert_bytes')(self.name, value,
                                                                    op="write")
        value = object.__getattribute__(instance, '_convert_json')(self.name, value,
                                                                   op="dumps")
        instance._internal_set(self.name, value)
        object.__getattribute__(instance, "set_save_status")(False)


class PkDescriptor:

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        value = object.__getattribute__(instance, "__dict__").get(self.name, None)
        value = object.__getattribute__(instance, "_convert_json")(self.name, value,
                                                                   "loads")
        value = object.__getattribute__(instance, "_convert_bytes")(self.name, value,
                                                                    "read")
        return value

    def __set__(self, instance, value):
        if self.name in object.__getattribute__(instance, "_choices_fields"):
            validate_choices(field=instance.Meta.model_fields[self.name], value=value)
        value = object.__getattribute__(instance, '_convert_bytes')(self.name, value,
                                                                    op="write")
        value = object.__getattribute__(instance, '_convert_json')(self.name, value,
                                                                   op="dumps")
        instance._internal_set(self.name, value)
        object.__getattribute__(instance, "set_save_status")(False)


class RelationDescriptor:

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if self.name in object.__getattribute__(instance, '_orm'):
            return object.__getattribute__(instance, '_orm').get(
                self.name)  # type: ignore
        return None  # pragma no cover

    def __set__(self, instance, value):
        model = (
            object.__getattribute__(instance, "Meta")
                .model_fields[self.name]
                .expand_relationship(value=value, child=instance)
        )
        if isinstance(object.__getattribute__(instance, "__dict__").get(self.name),
                      list):
            # virtual foreign key or many to many
            # TODO: Fix double items in dict, no effect on real action ugly repr
            # if model.pk not in [x.pk for  x in related_list]:
            object.__getattribute__(instance, "__dict__")[self.name].append(model)
        else:
            # foreign key relation
            object.__getattribute__(instance, "__dict__")[self.name] = model
            object.__getattribute__(instance, "set_save_status")(False)


class PropertyDescriptor:

    def __init__(self, name, function):
        self.name = name
        self.function = function

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance is not None and self.function is not None:
            bound = self.function.__get__(instance, instance.__class__)
            return bound() if callable(bound) else bound

    def __set__(self, instance, value):
        pass
