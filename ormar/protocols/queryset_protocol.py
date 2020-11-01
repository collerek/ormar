from typing import Any, List, Optional, Sequence, TYPE_CHECKING, Union

try:
    from typing import Protocol
except ImportError:  # pragma: nocover
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:  # noqa: C901; #pragma nocover
    from ormar import QuerySet, Model


class QuerySetProtocol(Protocol):  # pragma: nocover
    def filter(self, **kwargs: Any) -> "QuerySet":  # noqa: A003, A001
        ...

    def select_related(self, related: Union[List, str]) -> "QuerySet":
        ...

    async def exists(self) -> bool:
        ...

    async def count(self) -> int:
        ...

    async def clear(self) -> int:
        ...

    def limit(self, limit_count: int) -> "QuerySet":
        ...

    def offset(self, offset: int) -> "QuerySet":
        ...

    async def first(self, **kwargs: Any) -> "Model":
        ...

    async def get(self, **kwargs: Any) -> "Model":
        ...

    async def all(  # noqa: A003, A001
        self, **kwargs: Any
    ) -> Sequence[Optional["Model"]]:
        ...

    async def create(self, **kwargs: Any) -> "Model":
        ...
