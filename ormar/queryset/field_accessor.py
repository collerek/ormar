from typing import Any

from ormar.queryset.actions import OrderAction
from ormar.queryset.actions.filter_action import METHODS_TO_OPERATORS
from ormar.queryset.clause import FilterGroup


class FieldAccessor:
    def __init__(
        self, source_model=None, field=None, model=None, access_chain: str = ""
    ):
        self._source_model = source_model
        self._field = field
        self._model = model
        self._access_chain = access_chain

    def __bool__(self):
        # hack to avoid pydantic name check from parent model
        return False

    def __getattr__(self, item: str) -> Any:
        if self._field and item == self._field.name:
            return self._field

        if item in self._model.Meta.model_fields:
            field = self._model.Meta.model_fields.get(item)
            if field.is_relation:
                return FieldAccessor(
                    source_model=self._source_model,
                    model=field.to,
                    access_chain=self._access_chain + f"__{item}",
                )
            else:
                return FieldAccessor(
                    source_model=self._source_model,
                    field=field,
                    access_chain=self._access_chain + f"__{item}",
                )
        return object.__getattribute__(self, item)  # pragma: no cover

    def _check_field(self) -> None:
        if not self._field:
            raise AttributeError(
                "Cannot filter by Model, you need to provide model name"
            )

    def _select_operator(self, op: str, other: Any) -> FilterGroup:
        self._check_field()
        filter_kwg = {self._access_chain + f"__{METHODS_TO_OPERATORS[op]}": other}
        return FilterGroup(**filter_kwg)

    def __eq__(self, other: Any) -> FilterGroup:  # type: ignore
        return self._select_operator(op="__eq__", other=other)

    def __ge__(self, other: Any) -> FilterGroup:
        return self._select_operator(op="__ge__", other=other)

    def __gt__(self, other: Any) -> FilterGroup:
        return self._select_operator(op="__gt__", other=other)

    def __le__(self, other: Any) -> FilterGroup:
        return self._select_operator(op="__le__", other=other)

    def __lt__(self, other) -> FilterGroup:
        return self._select_operator(op="__lt__", other=other)

    def __mod__(self, other) -> FilterGroup:
        return self._select_operator(op="__mod__", other=other)

    def __lshift__(self, other) -> FilterGroup:
        return self._select_operator(op="in", other=other)

    def __rshift__(self, other) -> FilterGroup:
        return self._select_operator(op="isnull", other=True)

    def in_(self, other) -> FilterGroup:
        return self._select_operator(op="in", other=other)

    def iexact(self, other) -> FilterGroup:
        return self._select_operator(op="iexact", other=other)

    def contains(self, other) -> FilterGroup:
        return self._select_operator(op="contains", other=other)

    def icontains(self, other) -> FilterGroup:
        return self._select_operator(op="icontains", other=other)

    def startswith(self, other) -> FilterGroup:
        return self._select_operator(op="startswith", other=other)

    def istartswith(self, other) -> FilterGroup:
        return self._select_operator(op="istartswith", other=other)

    def endswith(self, other) -> FilterGroup:
        return self._select_operator(op="endswith", other=other)

    def iendswith(self, other) -> FilterGroup:
        return self._select_operator(op="iendswith", other=other)

    def isnull(self, other) -> FilterGroup:
        return self._select_operator(op="isnull", other=other)

    def asc(self) -> OrderAction:
        return OrderAction(order_str=self._access_chain, model_cls=self._source_model)

    def desc(self) -> OrderAction:
        return OrderAction(
            order_str="-" + self._access_chain, model_cls=self._source_model
        )
