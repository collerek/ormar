from ormar.models.mixins import (
    ExcludableMixin,
    MergeModelMixin,
    PydanticMixin,
    SavePrepareMixin,
)


class ModelTableProxy(
    MergeModelMixin,
    SavePrepareMixin,
    ExcludableMixin,
    PydanticMixin,
):
    """
    Used to combine all mixins with different set of functionalities.
    One of the bases of the ormar Model class.
    """
