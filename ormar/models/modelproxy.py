from ormar.models.mixins import (
    ExcludableMixin,
    MergeModelMixin,
    PrefetchQueryMixin,
    SavePrepareMixin,
)


class ModelTableProxy(
    PrefetchQueryMixin, MergeModelMixin, SavePrepareMixin, ExcludableMixin
):
    """
    Used to combine all mixins with different set of functionalities.
    One of the bases of the ormar Model class.
    """
