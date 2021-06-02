"""
Package contains functionalities divided by features.
All mixins are combined into ModelTableProxy which is one of the parents of Model.
The split into mixins was done to ease the maintainability of the proxy class, as
it became quite complicated over time.
"""
from ormar.models.mixins.alias_mixin import AliasMixin
from ormar.models.mixins.excludable_mixin import ExcludableMixin
from ormar.models.mixins.merge_mixin import MergeModelMixin
from ormar.models.mixins.prefetch_mixin import PrefetchQueryMixin
from ormar.models.mixins.pydantic_mixin import PydanticMixin
from ormar.models.mixins.save_mixin import SavePrepareMixin

__all__ = [
    "MergeModelMixin",
    "AliasMixin",
    "PrefetchQueryMixin",
    "SavePrepareMixin",
    "ExcludableMixin",
    "PydanticMixin",
]
