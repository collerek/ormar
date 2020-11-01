from typing import Protocol, TYPE_CHECKING, Type, Union

if TYPE_CHECKING:  # pragma: nocover
    from ormar import Model


class RelationProtocol(Protocol):  # pragma: nocover
    def add(self, child: "Model") -> None:
        ...

    def remove(self, child: Union["Model", Type["Model"]]) -> None:
        ...
