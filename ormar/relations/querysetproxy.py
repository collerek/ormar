from typing import (
    Any,
    Dict,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

import ormar
from ormar.exceptions import ModelPersistenceError

if TYPE_CHECKING:  # pragma no cover
    from ormar.relations import Relation
    from ormar.models import Model
    from ormar.queryset import QuerySet
    from ormar import RelationType

    T = TypeVar("T", bound=Model)


class QuerysetProxy(ormar.QuerySetProtocol):
    """
    Exposes QuerySet methods on relations, but also handles creating and removing
    of through Models for m2m relations.
    """

    if TYPE_CHECKING:  # pragma no cover
        relation: "Relation"

    def __init__(
        self, relation: "Relation", type_: "RelationType", qryset: "QuerySet" = None
    ) -> None:
        self.relation: Relation = relation
        self._queryset: Optional["QuerySet"] = qryset
        self.type_: "RelationType" = type_
        self._owner: "Model" = self.relation.manager.owner
        self.related_field_name = self._owner.Meta.model_fields[
            self.relation.field_name
        ].get_related_name()
        self.related_field = self.relation.to.Meta.model_fields[self.related_field_name]
        self.owner_pk_value = self._owner.pk

    @property
    def queryset(self) -> "QuerySet":
        """
        Returns queryset if it's set, AttributeError otherwise.
        :return: QuerySet
        :rtype: QuerySet
        """
        if not self._queryset:
            raise AttributeError
        return self._queryset

    @queryset.setter
    def queryset(self, value: "QuerySet") -> None:
        """
        Set's the queryset. Initialized in RelationProxy.
        :param value: QuerySet
        :type value: QuerySet
        """
        self._queryset = value

    def _assign_child_to_parent(self, child: Optional["T"]) -> None:
        """
        Registers child in parents RelationManager.

        :param child: child to register on parent side.
        :type child: Model
        """
        if child:
            owner = self._owner
            rel_name = self.relation.field_name
            setattr(owner, rel_name, child)

    def _register_related(self, child: Union["T", Sequence[Optional["T"]]]) -> None:
        """
        Registers child/ children in parents RelationManager.

        :param child: child or list of children models to register.
        :type child: Union[Model,List[Model]]
        """
        if isinstance(child, list):
            for subchild in child:
                self._assign_child_to_parent(subchild)
        else:
            assert isinstance(child, ormar.Model)
            self._assign_child_to_parent(child)

    def _clean_items_on_load(self) -> None:
        """
        Cleans the current list of the related models.
        """
        if isinstance(self.relation.related_models, MutableSequence):
            for item in self.relation.related_models[:]:
                self.relation.remove(item)

    async def create_through_instance(self, child: "T") -> None:
        """
        Crete a through model instance in the database for m2m relations.

        :param child: child model instance
        :type child: Model
        """
        model_cls = self.relation.through
        owner_column = self.related_field.default_target_field_name()  # type: ignore
        child_column = self.related_field.default_source_field_name()  # type: ignore
        kwargs = {owner_column: self._owner.pk, child_column: child.pk}
        if child.pk is None:
            raise ModelPersistenceError(
                f"You cannot save {child.get_name()} "
                f"model without primary key set! \n"
                f"Save the child model first."
            )
        expr = model_cls.Meta.table.insert()
        expr = expr.values(**kwargs)
        # print("\n", expr.compile(compile_kwargs={"literal_binds": True}))
        await model_cls.Meta.database.execute(expr)

    async def delete_through_instance(self, child: "T") -> None:
        """
        Removes through model instance from the database for m2m relations.

        :param child: child model instance
        :type child: Model
        """
        queryset = ormar.QuerySet(model_cls=self.relation.through)
        owner_column = self.related_field.default_target_field_name()  # type: ignore
        child_column = self.related_field.default_source_field_name()  # type: ignore
        kwargs = {owner_column: self._owner, child_column: child}
        link_instance = await queryset.filter(**kwargs).get()  # type: ignore
        await link_instance.delete()

    async def exists(self) -> bool:
        """
        Returns a bool value to confirm if there are rows matching the given criteria
        (applied with `filter` and `exclude` if set).

        Actual call delegated to QuerySet.

        :return: result of the check
        :rtype: bool
        """
        return await self.queryset.exists()

    async def count(self) -> int:
        """
        Returns number of rows matching the given criteria
        (applied with `filter` and `exclude` if set before).

        Actual call delegated to QuerySet.

        :return: number of rows
        :rtype: int
        """
        return await self.queryset.count()

    async def clear(self, keep_reversed: bool = True) -> int:
        """
        Removes all related models from given relation.

        Removes all through models for m2m relation.

        For reverse FK relations keep_reversed flag marks if the reversed models
        should be kept or deleted from the database too (False means that models
        will be deleted, and not only removed from relation).

        :param keep_reversed: flag if reverse models in reverse FK should be deleted
        or not, keep_reversed=False deletes them from database.
        :type keep_reversed: bool
        :return: number of deleted models
        :rtype: int
        """
        if self.type_ == ormar.RelationType.MULTIPLE:
            queryset = ormar.QuerySet(model_cls=self.relation.through)
            owner_column = self._owner.get_name()
        else:
            queryset = ormar.QuerySet(model_cls=self.relation.to)
            owner_column = self.related_field.name
        kwargs = {owner_column: self._owner}
        self._clean_items_on_load()
        if keep_reversed and self.type_ == ormar.RelationType.REVERSE:
            update_kwrgs = {f"{owner_column}": None}
            return await queryset.filter(_exclude=False, **kwargs).update(
                each=False, **update_kwrgs
            )
        return await queryset.delete(**kwargs)  # type: ignore

    async def first(self, **kwargs: Any) -> "Model":
        """
        Gets the first row from the db ordered by primary key column ascending.

        Actual call delegated to QuerySet.

        List of related models is cleared before the call.

        :param kwargs:
        :type kwargs:
        :return:
        :rtype: _asyncio.Future
        """
        first = await self.queryset.first(**kwargs)
        self._clean_items_on_load()
        self._register_related(first)
        return first

    async def get(self, **kwargs: Any) -> "Model":
        """
        Get's the first row from the db meeting the criteria set by kwargs.

        If no criteria set it will return the last row in db sorted by pk.

        Passing a criteria is actually calling filter(**kwargs) method described below.

        Actual call delegated to QuerySet.

        List of related models is cleared before the call.

        :raises NoMatch: if no rows are returned
        :raises MultipleMatches: if more than 1 row is returned.
        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: returned model
        :rtype: Model
        """
        get = await self.queryset.get(**kwargs)
        self._clean_items_on_load()
        self._register_related(get)
        return get

    async def all(self, **kwargs: Any) -> Sequence[Optional["Model"]]:  # noqa: A003
        """
        Returns all rows from a database for given model for set filter options.

        Passing kwargs is a shortcut and equals to calling `filter(**kwrags).all()`.

        If there are no rows meeting the criteria an empty list is returned.

        Actual call delegated to QuerySet.

        List of related models is cleared before the call.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: list of returned models
        :rtype: List[Model]
        """
        all_items = await self.queryset.all(**kwargs)
        self._clean_items_on_load()
        self._register_related(all_items)
        return all_items

    async def create(self, **kwargs: Any) -> "Model":
        """
        Creates the model instance, saves it in a database and returns the updates model
        (with pk populated if not passed and autoincrement is set).

        The allowed kwargs are `Model` fields names and proper value types.

        For m2m relation the through model is created automatically.

        Actual call delegated to QuerySet.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: created model
        :rtype: Model
        """
        if self.type_ == ormar.RelationType.REVERSE:
            kwargs[self.related_field.name] = self._owner
        created = await self.queryset.create(**kwargs)
        self._register_related(created)
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.create_through_instance(created)
        return created

    async def get_or_create(self, **kwargs: Any) -> "Model":
        """
        Combination of create and get methods.

        Tries to get a row meeting the criteria fro kwargs
        and if `NoMatch` exception is raised
        it creates a new one with given kwargs.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: returned or created Model
        :rtype: Model
        """
        try:
            return await self.get(**kwargs)
        except ormar.NoMatch:
            return await self.create(**kwargs)

    async def update_or_create(self, **kwargs: Any) -> "Model":
        """
        Updates the model, or in case there is no match in database creates a new one.

        Actual call delegated to QuerySet.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: updated or created model
        :rtype: Model
        """
        pk_name = self.queryset.model_meta.pkname
        if "pk" in kwargs:
            kwargs[pk_name] = kwargs.pop("pk")
        if pk_name not in kwargs or kwargs.get(pk_name) is None:
            return await self.create(**kwargs)
        model = await self.queryset.get(pk=kwargs[pk_name])
        return await model.update(**kwargs)

    def filter(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        """
        Allows you to filter by any `Model` attribute/field
        as well as to fetch instances, with a filter across an FK relationship.

        You can use special filter suffix to change the filter operands:

        *  exact - like `album__name__exact='Malibu'` (exact match)
        *  iexact - like `album__name__iexact='malibu'` (exact match case insensitive)
        *  contains - like `album__name__contains='Mal'` (sql like)
        *  icontains - like `album__name__icontains='mal'` (sql like case insensitive)
        *  in - like `album__name__in=['Malibu', 'Barclay']` (sql in)
        *  gt - like `position__gt=3` (sql >)
        *  gte - like `position__gte=3` (sql >=)
        *  lt - like `position__lt=3` (sql <)
        *  lte - like `position__lte=3` (sql <=)
        *  startswith - like `album__name__startswith='Mal'` (exact start match)
        *  istartswith - like `album__name__istartswith='mal'` (case insensitive)
        *  endswith - like `album__name__endswith='ibu'` (exact end match)
        *  iendswith - like `album__name__iendswith='IBU'` (case insensitive)

        Actual call delegated to QuerySet.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: filtered QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.filter(**kwargs)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def exclude(self, **kwargs: Any) -> "QuerysetProxy":  # noqa: A003, A001
        """
        Works exactly the same as filter and all modifiers (suffixes) are the same,
        but returns a *not* condition.

        So if you use `filter(name='John')` which is `where name = 'John'` in SQL,
        the `exclude(name='John')` equals to `where name <> 'John'`

        Note that all conditions are joined so if you pass multiple values it
        becomes a union of conditions.

        `exclude(name='John', age>=35)` will become
        `where not (name='John' and age>=35)`

        Actual call delegated to QuerySet.

        :param kwargs: fields names and proper value types
        :type kwargs: Any
        :return: filtered QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.exclude(**kwargs)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def select_related(self, related: Union[List, str]) -> "QuerysetProxy":
        """
        Allows to prefetch related models during the same query.

        **With `select_related` always only one query is run against the database**,
        meaning that one (sometimes complicated) join is generated and later nested
        models are processed in python.

        To fetch related model use `ForeignKey` names.

        To chain related `Models` relation use double underscores between names.

        Actual call delegated to QuerySet.

        :param related: list of relation field names, can be linked by '__' to nest
        :type related: Union[List, str]
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.select_related(related)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def prefetch_related(self, related: Union[List, str]) -> "QuerysetProxy":
        """
        Allows to prefetch related models during query - but opposite to
        `select_related` each subsequent model is fetched in a separate database query.

        **With `prefetch_related` always one query per Model is run against the
        database**, meaning that you will have multiple queries executed one
        after another.

        To fetch related model use `ForeignKey` names.

        To chain related `Models` relation use double underscores between names.

        Actual call delegated to QuerySet.

        :param related: list of relation field names, can be linked by '__' to nest
        :type related: Union[List, str]
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.prefetch_related(related)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def paginate(self, page: int, page_size: int = 20) -> "QuerysetProxy":
        """
        You can paginate the result which is a combination of offset and limit clauses.
        Limit is set to page size and offset is set to (page-1) * page_size.

        Actual call delegated to QuerySet.

        :param page_size: numbers of items per page
        :type page_size: int
        :param page: page number
        :type page: int
        :return: QuerySet
        :rtype: QuerySet
        """
        queryset = self.queryset.paginate(page=page, page_size=page_size)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def limit(self, limit_count: int) -> "QuerysetProxy":
        """
        You can limit the results to desired number of parent models.

        Actual call delegated to QuerySet.

        :param limit_count: number of models to limit
        :type limit_count: int
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.limit(limit_count)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def offset(self, offset: int) -> "QuerysetProxy":
        """
        You can also offset the results by desired number of main models.

        Actual call delegated to QuerySet.

        :param offset: numbers of models to offset
        :type offset: int
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.offset(offset)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        """
        With `fields()` you can select subset of model columns to limit the data load.

        Note that `fields()` and `exclude_fields()` works both for main models
        (on normal queries like `get`, `all` etc.)
        as well as `select_related` and `prefetch_related`
        models (with nested notation).

        You can select specified fields by passing a `str, List[str], Set[str] or
        dict` with nested definition.

        To include related models use notation
        `{related_name}__{column}[__{optional_next} etc.]`.

        `fields()` can be called several times, building up the columns to select.

        If you include related models into `select_related()` call but you won't specify
        columns for those models in fields - implies a list of all fields for
        those nested models.

        Mandatory fields cannot be excluded as it will raise `ValidationError`,
         to exclude a field it has to be nullable.

        Pk column cannot be excluded - it's always auto added even if
        not explicitly included.

        You can also pass fields to include as dictionary or set.

        To mark a field as included in a dictionary use it's name as key
        and ellipsis as value.

        To traverse nested models use nested dictionaries.

        To include fields at last level instead of nested dictionary a set can be used.

        To include whole nested model specify model related field name and ellipsis.

        Actual call delegated to QuerySet.

        :param columns: columns to include
        :type columns: Union[List, str, Set, Dict]
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.fields(columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def exclude_fields(self, columns: Union[List, str, Set, Dict]) -> "QuerysetProxy":
        """
        With `exclude_fields()` you can select subset of model columns that will
        be excluded to limit the data load.

        It's the opposite of `fields()` method so check documentation above
        to see what options are available.

        Especially check above how you can pass also nested dictionaries
        and sets as a mask to exclude fields from whole hierarchy.

        Note that `fields()` and `exclude_fields()` works both for main models
        (on normal queries like `get`, `all` etc.)
        as well as `select_related` and `prefetch_related` models
        (with nested notation).

        Mandatory fields cannot be excluded as it will raise `ValidationError`,
        to exclude a field it has to be nullable.

        Pk column cannot be excluded - it's always auto added even
        if explicitly excluded.

        Actual call delegated to QuerySet.

        :param columns: columns to exclude
        :type columns: Union[List, str, Set, Dict]
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.exclude_fields(columns=columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)

    def order_by(self, columns: Union[List, str]) -> "QuerysetProxy":
        """
        With `order_by()` you can order the results from database based on your
        choice of fields.

        You can provide a string with field name or list of strings with fields names.

        Ordering in sql will be applied in order of names you provide in order_by.

        By default if you do not provide ordering `ormar` explicitly orders by
        all primary keys

        If you are sorting by nested models that causes that the result rows are
        unsorted by the main model `ormar` will combine those children rows into
        one main model.

        The main model will never duplicate in the result

        To order by main model field just provide a field name

        To sort on nested models separate field names with dunder '__'.

        You can sort this way across all relation types -> `ForeignKey`,
        reverse virtual FK and `ManyToMany` fields.

        To sort in descending order provide a hyphen in front of the field name

        Actual call delegated to QuerySet.

        :param columns: columns by which models should be sorted
        :type columns: Union[List, str]
        :return: QuerysetProxy
        :rtype: QuerysetProxy
        """
        queryset = self.queryset.order_by(columns)
        return self.__class__(relation=self.relation, type_=self.type_, qryset=queryset)
