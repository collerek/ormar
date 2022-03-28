from typing import Any, Dict, List, Optional, Sequence, Set, TYPE_CHECKING, Tuple, Union

try:
    from typing import Protocol
except ImportError:  # pragma: nocover
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:  # noqa: C901; #pragma nocover
    from ormar import Model
    from ormar.relations.querysetproxy import QuerysetProxy


class QuerySetProtocol(Protocol):  # pragma: nocover
    def filter(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        ...

    def exclude(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        ...

    def select_related(self, related: Union[List, str]) -> "QuerysetProxy":
        ...

    def prefetch_related(self, related: Union[List, str]) -> "QuerysetProxy":
        ...

    async def exists(self) -> bool:
        ...

    async def count(self, distinct: bool = True) -> int:
        ...

    async def clear(self) -> int:
        ...

    def limit(self, limit_count: int) -> "QuerysetProxy":
        ...

    def offset(self, offset: int) -> "QuerysetProxy":
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

    async def update(self, each: bool = False, **kwargs: Any) -> int:
        ...

    async def get_or_create(
        self,
        _defaults: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple["Model", bool]:
        ...

    async def update_or_create(self, **kwargs: Any) -> "Model":
        ...

    def fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        ...

    def exclude_fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        ...

    def order_by(self, columns: Union[List, str]) -> "QuerysetProxy":
        ...
