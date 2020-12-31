import ormar  # noqa:  I100
from ormar.models.mixins import (
    AliasMixin,
    ExcludableMixin,
    MergeModelMixin,
    PrefetchQueryMixin,
    SavePrepareMixin,
)


class ModelTableProxy(
    PrefetchQueryMixin, MergeModelMixin, AliasMixin, SavePrepareMixin, ExcludableMixin
):
    pass
