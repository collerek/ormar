from typing import Any, Generic, Optional, TYPE_CHECKING, Type, TypeVar

import ormar
from ormar.exceptions import NoMatch, RelationshipInstanceError
from ormar.relations.querysetproxy import QuerysetProxy

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model, RelationType
    from ormar.models import T
    from ormar.relations import Relation
    from ormar.queryset import QuerySet
else:
    T = TypeVar("T", bound="Model")


class RelationProxy(Generic[T], list):
    """
    Proxy of the Relation that is a list with special methods.
    """

    def __init__(
        self,
        relation: "Relation",
        type_: "RelationType",
        to: Type["T"],
        field_name: str,
        data_: Any = None,
    ) -> None:
        super().__init__(data_ or ())
        self.relation: "Relation[T]" = relation
        self.type_: "RelationType" = type_
        self.field_name = field_name
        self._owner: "Model" = self.relation.manager.owner
        self.queryset_proxy: QuerysetProxy[T] = QuerysetProxy[T](
            relation=self.relation, to=to, type_=type_
        )
        self._related_field_name: Optional[str] = None

    @property
    def related_field_name(self) -> str:
        """
        On first access calculates the name of the related field, later stored in
        _related_field_name property.

        :return: name of the related field
        :rtype: str
        """
        if self._related_field_name:
            return self._related_field_name
        owner_field = self._owner.Meta.model_fields[self.field_name]
        self._related_field_name = owner_field.get_related_name()

        return self._related_field_name

    def __getitem__(self, item: Any) -> "T":  # type: ignore
        return super().__getitem__(item)

    def __getattribute__(self, item: str) -> Any:
        """
        Since some QuerySetProxy methods overwrite builtin list methods we
        catch calls to them and delegate it to QuerySetProxy instead.

        :param item: name of attribute
        :type item: str
        :return: value of attribute
        :rtype: Any
        """
        if item in ["count", "clear"]:
            self._initialize_queryset()
            return getattr(self.queryset_proxy, item)
        return super().__getattribute__(item)

    def __getattr__(self, item: str) -> Any:
        """
        Delegates calls for non existing attributes to QuerySetProxy.

        :param item: name of attribute/method
        :type item: str
        :return: method from QuerySetProxy if exists
        :rtype: method
        """
        self._initialize_queryset()
        return getattr(self.queryset_proxy, item)

    def _clear(self) -> None:
        super().clear()

    def _initialize_queryset(self) -> None:
        """
        Initializes the QuerySetProxy if not yet initialized.
        """
        if not self._check_if_queryset_is_initialized():
            self.queryset_proxy.queryset = self._set_queryset()

    def _check_if_queryset_is_initialized(self) -> bool:
        """
        Checks if the QuerySetProxy is already set and ready.
        :return: result of the check
        :rtype: bool
        """
        return (
            hasattr(self.queryset_proxy, "queryset")
            and self.queryset_proxy.queryset is not None
        )

    def _check_if_model_saved(self) -> None:
        """
        Verifies if the parent model of the relation has been already saved.
        Otherwise QuerySetProxy cannot filter by parent primary key.
        """
        pk_value = self._owner.pk
        if not pk_value:
            raise RelationshipInstanceError(
                "You cannot query relationships from unsaved model."
            )

    def _set_queryset(self) -> "QuerySet[T]":
        """
        Creates new QuerySet with relation model and pre filters it with currents
        parent model primary key, so all queries by definition are already related
        to the parent model only, without need for user to filter them.

        :return: initialized QuerySet
        :rtype: QuerySet
        """
        related_field_name = self.related_field_name
        pkname = self._owner.get_column_alias(self._owner.Meta.pkname)
        self._check_if_model_saved()
        kwargs = {f"{related_field_name}__{pkname}": self._owner.pk}
        queryset = (
            ormar.QuerySet(
                model_cls=self.relation.to, proxy_source_model=self._owner.__class__
            )
            .select_related(related_field_name)
            .filter(**kwargs)
        )
        return queryset

    async def remove(  # type: ignore
        self, item: "T", keep_reversed: bool = True
    ) -> None:
        """
        Removes the related from relation with parent.

        Through models are automatically deleted for m2m relations.

        For reverse FK relations keep_reversed flag marks if the reversed models
        should be kept or deleted from the database too (False means that models
        will be deleted, and not only removed from relation).

        :param item: child to remove from relation
        :type item: Model
        :param keep_reversed: flag if the reversed model should be kept or deleted too
        :type keep_reversed: bool
        """
        if item not in self:
            raise NoMatch(
                f"Object {self._owner.get_name()} has no "
                f"{item.get_name()} with given primary key!"
            )
        await self._owner.signals.pre_relation_remove.send(
            sender=self._owner.__class__,
            instance=self._owner,
            child=item,
            relation_name=self.field_name,
        )
        super().remove(item)
        relation_name = self.related_field_name
        relation = item._orm._get(relation_name)
        # if relation is None:  # pragma nocover
        #     raise ValueError(
        #         f"{self._owner.get_name()} does not have relation {relation_name}"
        #     )
        if relation:
            relation.remove(self._owner)
        self.relation.remove(item)
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.delete_through_instance(item)
        else:
            if keep_reversed:
                setattr(item, relation_name, None)
                await item.update()
            else:
                await item.delete()
        await self._owner.signals.post_relation_remove.send(
            sender=self._owner.__class__,
            instance=self._owner,
            child=item,
            relation_name=self.field_name,
        )

    async def add(self, item: "T", **kwargs: Any) -> None:
        """
        Adds child model to relation.

        For ManyToMany relations through instance is automatically created.

        :param kwargs: dict of additional keyword arguments for through instance
        :type kwargs: Any
        :param item: child to add to relation
        :type item: Model
        """
        relation_name = self.related_field_name
        await self._owner.signals.pre_relation_add.send(
            sender=self._owner.__class__,
            instance=self._owner,
            child=item,
            relation_name=self.field_name,
            passed_kwargs=kwargs,
        )
        self._check_if_model_saved()
        if self.type_ == ormar.RelationType.MULTIPLE:
            await self.queryset_proxy.create_through_instance(item, **kwargs)
            setattr(self._owner, self.field_name, item)
        else:
            setattr(item, relation_name, self._owner)
            await item.upsert()
        await self._owner.signals.post_relation_add.send(
            sender=self._owner.__class__,
            instance=self._owner,
            child=item,
            relation_name=self.field_name,
            passed_kwargs=kwargs,
        )
