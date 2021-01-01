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
    """
    Used to combine all mixins with different set of functionalities.
    One of the bases of the ormar Model class.
    """
