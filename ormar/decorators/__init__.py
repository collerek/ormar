"""
Module with all decorators that are exposed for users.

Currently only:

* property_field - exposing @property like function as field in Model.dict()
* predefined signals decorators (pre/post + save/update/delete)

"""
from ormar.decorators.property_field import property_field
from ormar.decorators.signals import (
    post_bulk_update,
    post_delete,
    post_relation_add,
    post_relation_remove,
    post_save,
    post_update,
    pre_delete,
    pre_relation_add,
    pre_relation_remove,
    pre_save,
    pre_update,
)

__all__ = [
    "property_field",
    "post_bulk_update",
    "post_delete",
    "post_save",
    "post_update",
    "pre_delete",
    "pre_save",
    "pre_update",
    "post_relation_remove",
    "post_relation_add",
    "pre_relation_remove",
    "pre_relation_add",
]
