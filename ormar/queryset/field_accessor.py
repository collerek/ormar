from typing import Any, Optional, TYPE_CHECKING, Type, cast

from ormar.queryset.actions import OrderAction
from ormar.queryset.actions.filter_action import METHODS_TO_OPERATORS
from ormar.queryset.clause import FilterGroup, NullsOrdering

if TYPE_CHECKING:  # pragma: no cover
    from ormar import BaseField, Model


class FieldAccessor:
    """
    Helper to access ormar fields directly from Model class also for nested
    models attributes.
    """

    def __init__(
        self,
        source_model: Type["Model"],
        field: "BaseField" = None,
        model: Type["Model"] = None,
        access_chain: str = "",
    ) -> None:
        self._source_model = source_model
        self._field = field
        self._model = model
        self._access_chain = access_chain

    def __bool__(self) -> bool:
        """
        Hack to avoid pydantic name check from parent model, returns false

        :return: False
        :rtype: bool
        """
        return False

    def __getattr__(self, item: str) -> Any:
        """
        Accessor return new accessor for each field and nested models.
        Thanks to that operator overload is possible to use in filter.

        :param item: attribute name
        :type item: str
        :return: FieldAccessor for field or nested model
        :rtype: ormar.queryset.field_accessor.FieldAccessor
        """
        if (
            object.__getattribute__(self, "_field")
            and item == object.__getattribute__(self, "_field").name
        ):
            return self._field

        if (
            object.__getattribute__(self, "_model")
            and item in object.__getattribute__(self, "_model").Meta.model_fields
        ):
            field = cast("Model", self._model).Meta.model_fields[item]
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
        """
        overloaded to work as sql `column = <VALUE>`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__eq__", other=other)

    def __ge__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column >= <VALUE>`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__ge__", other=other)

    def __gt__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column > <VALUE>`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__gt__", other=other)

    def __le__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column <= <VALUE>`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__le__", other=other)

    def __lt__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column < <VALUE>`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__lt__", other=other)

    def __mod__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column LIKE '%<VALUE>%'`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="__mod__", other=other)

    def __lshift__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column IN (<VALUE1>, <VALUE2>,...)`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="in", other=other)

    def __rshift__(self, other: Any) -> FilterGroup:
        """
        overloaded to work as sql `column IS NULL`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="isnull", other=True)

    def in_(self, other: Any) -> FilterGroup:
        """
        works as sql `column IN (<VALUE1>, <VALUE2>,...)`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="in", other=other)

    def iexact(self, other: Any) -> FilterGroup:
        """
        works as sql `column = <VALUE>` case-insensitive

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="iexact", other=other)

    def contains(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '%<VALUE>%'`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="contains", other=other)

    def icontains(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '%<VALUE>%'` case-insensitive

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="icontains", other=other)

    def startswith(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '<VALUE>%'`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="startswith", other=other)

    def istartswith(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '%<VALUE>'` case-insensitive

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="istartswith", other=other)

    def endswith(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '%<VALUE>'`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="endswith", other=other)

    def iendswith(self, other: Any) -> FilterGroup:
        """
        works as sql `column LIKE '%<VALUE>'` case-insensitive

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="iendswith", other=other)

    def isnull(self, other: Any) -> FilterGroup:
        """
        works as sql `column IS NULL` or `IS NOT NULL`

        :param other: value to check agains operator
        :type other: str
        :return: FilterGroup for operator
        :rtype: ormar.queryset.clause.FilterGroup
        """
        return self._select_operator(op="isnull", other=other)

    def asc(self, nulls_ordering: Optional[NullsOrdering] = None) -> OrderAction:
        """
        works as sql `column asc`

        :param nulls_ordering: nulls ordering option first or last, defaults to None
        :type nulls_ordering: Optional[NullsOrdering], optional
        :raises ValueError: if nulls_ordering is not None or NullsOrdering Enum
        :return: OrderGroup for operator
        :rtype: ormar.queryset.actions.OrderGroup
        """
        if nulls_ordering is not None and not isinstance(nulls_ordering, NullsOrdering):
            raise ValueError("Invalid option for ordering nulls values.")

        return OrderAction(
            order_str=self._access_chain,
            model_cls=self._source_model,
            nulls_ordering=nulls_ordering.value if nulls_ordering is not None else None,
        )

    def desc(self, nulls_ordering: Optional[NullsOrdering] = None) -> OrderAction:
        """
        works as sql `column desc`

        :param nulls_ordering: nulls ordering option first or last, defaults to None
        :type nulls_ordering: Optional[NullsOrdering], optional
        :raises ValueError: if nulls_ordering is not None or NullsOrdering Enum
        :return: OrderGroup for operator
        :rtype: ormar.queryset.actions.OrderGroup
        """
        if nulls_ordering is not None and not isinstance(nulls_ordering, NullsOrdering):
            raise ValueError("Invalid option for ordering nulls values.")

        return OrderAction(
            order_str="-" + self._access_chain,
            model_cls=self._source_model,
            nulls_ordering=nulls_ordering.value if nulls_ordering is not None else None,
        )
