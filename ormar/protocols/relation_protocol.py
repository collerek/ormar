from typing import TYPE_CHECKING, Type, Union

try:
    from typing import Protocol
except ImportError:  # pragma: nocover
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:  # pragma: nocover
    from ormar import Model


class RelationProtocol(Protocol):  # pragma: nocover
    def add(self, child: "Model") -> None:
        ...

    def remove(self, child: Union["Model", Type["Model"]]) -> None:
        ...
