from typing import (
    Any,
    Dict,
    List,
    Set,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
)

import ormar.queryset  # noqa I100
from ormar.exceptions import ModelPersistenceError, NoMatch
from ormar.models import NewBaseModel  # noqa I100
from ormar.models.metaclass import ModelMeta
from ormar.models.model_row import ModelRow

if TYPE_CHECKING:  # pragma nocover
    from ormar import QuerySet

T = TypeVar("T", bound="Model")


class Model(ModelRow):
    __abstract__ = False
    if TYPE_CHECKING:  # pragma nocover
        Meta: ModelMeta
        objects: "QuerySet"

    def __repr__(self) -> str:  # pragma nocover
        _repr = {k: getattr(self, k) for k, v in self.Meta.model_fields.items()}
        return f"{self.__class__.__name__}({str(_repr)})"

    async def upsert(self: T, **kwargs: Any) -> T:
        """
        Performs either a save or an update depending on the presence of the pk.
        If the pk field is filled it's an update, otherwise the save is performed.
        For save kwargs are ignored, used only in update if provided.

        :param kwargs: list of fields to update
        :type kwargs: Any
        :return: saved Model
        :rtype: Model
        """
        if not self.pk:
            return await self.save()
        return await self.update(**kwargs)

    async def save(self: T) -> T:
        """
        Performs a save of given Model instance.
        If primary key is already saved, db backend will throw integrity error.

        Related models are saved by pk number, reverse relation and many to many fields
        are not saved - use corresponding relations methods.

        If there are fields with server_default set and those fields
        are not already filled save will trigger also a second query
        to refreshed the fields populated server side.

        Does not recognize if model was previously saved.
        If you want to perform update or insert depending on the pk
        fields presence use upsert.

        Sends pre_save and post_save signals.

        Sets model save status to True.

        :return: saved Model
        :rtype: Model
        """
        await self.signals.pre_save.send(sender=self.__class__, instance=self)
        self_fields = self._extract_model_db_fields()

        if not self.pk and self.Meta.model_fields[self.Meta.pkname].autoincrement:
            self_fields.pop(self.Meta.pkname, None)
        self_fields = self.populate_default_values(self_fields)
        self.update_from_dict(
            {
                k: v
                for k, v in self_fields.items()
                if k not in self.extract_related_names()
            }
        )

        self_fields = self.translate_columns_to_aliases(self_fields)
        expr = self.Meta.table.insert()
        expr = expr.values(**self_fields)

        pk = await self.Meta.database.execute(expr)
        if pk and isinstance(pk, self.pk_type()):
            setattr(self, self.Meta.pkname, pk)

        self.set_save_status(True)
        # refresh server side defaults
        if any(
            field.server_default is not None
            for name, field in self.Meta.model_fields.items()
            if name not in self_fields
        ):
            await self.load()

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    async def save_related(  # noqa: CCR001
        self, follow: bool = False, visited: Set = None, update_count: int = 0
    ) -> int:  # noqa: CCR001
        """
        Triggers a upsert method on all related models
        if the instances are not already saved.
        By default saves only the directly related ones.

        If follow=True is set it saves also related models of related models.

        To not get stuck in an infinite loop as related models also keep a relation
        to parent model visited models set is kept.

        That way already visited models that are nested are saved, but the save do not
        follow them inside. So Model A -> Model B -> Model A -> Model C will save second
        Model A but will never follow into Model C.
        Nested relations of those kind need to be persisted manually.

        :param follow: flag to trigger deep save -
        by default only directly related models are saved
        with follow=True also related models of related models are saved
        :type follow: bool
        :param visited: internal parameter for recursive calls - already visited models
        :type visited: Set
        :param update_count: internal parameter for recursive calls -
        number of updated instances
        :type update_count: int
        :return: number of updated/saved models
        :rtype: int
        """
        if not visited:
            visited = {self.__class__}
        else:
            visited = {x for x in visited}
            visited.add(self.__class__)

        for related in self.extract_related_names():
            if (
                self.Meta.model_fields[related].virtual
                or self.Meta.model_fields[related].is_multi
            ):
                for rel in getattr(self, related):
                    update_count, visited = await self._update_and_follow(
                        rel=rel,
                        follow=follow,
                        visited=visited,
                        update_count=update_count,
                    )
                visited.add(self.Meta.model_fields[related].to)
            else:
                rel = getattr(self, related)
                update_count, visited = await self._update_and_follow(
                    rel=rel, follow=follow, visited=visited, update_count=update_count
                )
                visited.add(rel.__class__)
        return update_count

    @staticmethod
    async def _update_and_follow(
        rel: "Model", follow: bool, visited: Set, update_count: int
    ) -> Tuple[int, Set]:
        """
        Internal method used in save_related to follow related models and update numbers
        of updated related instances.

        :param rel: Model to follow
        :type rel: Model
        :param follow: flag to trigger deep save -
        by default only directly related models are saved
        with follow=True also related models of related models are saved
        :type follow: bool
        :param visited: internal parameter for recursive calls - already visited models
        :type visited: Set
        :param update_count: internal parameter for recursive calls -
        number of updated instances
        :type update_count: int
        :return: tuple of update count and visited
        :rtype: Tuple[int, Set]
        """
        if follow and rel.__class__ not in visited:
            update_count = await rel.save_related(
                follow=follow, visited=visited, update_count=update_count
            )
        if not rel.saved:
            await rel.upsert()
            update_count += 1
        return update_count, visited

    async def update(self: T, **kwargs: Any) -> T:
        """
        Performs update of Model instance in the database.
        Fields can be updated before or you can pass them as kwargs.

        Sends pre_update and post_update signals.

        Sets model save status to True.

        :raises ModelPersistenceError: If the pk column is not set

        :param kwargs: list of fields to update as field=value pairs
        :type kwargs: Any
        :return: updated Model
        :rtype: Model
        """
        if kwargs:
            self.update_from_dict(kwargs)

        if not self.pk:
            raise ModelPersistenceError(
                "You cannot update not saved model! Use save or upsert method."
            )

        await self.signals.pre_update.send(
            sender=self.__class__, instance=self, passed_args=kwargs
        )
        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.get_column_name_from_alias(self.Meta.pkname))
        self_fields = self.translate_columns_to_aliases(self_fields)
        expr = self.Meta.table.update().values(**self_fields)
        expr = expr.where(self.pk_column == getattr(self, self.Meta.pkname))

        await self.Meta.database.execute(expr)
        self.set_save_status(True)
        await self.signals.post_update.send(sender=self.__class__, instance=self)
        return self

    async def delete(self) -> int:
        """
        Removes the Model instance from the database.

        Sends pre_delete and post_delete signals.

        Sets model save status to False.

        Note it does not delete the Model itself (python object).
        So you can delete and later save (since pk is deleted no conflict will arise)
        or update and the Model will be saved in database again.

        :return: number of deleted rows (for some backends)
        :rtype: int
        """
        await self.signals.pre_delete.send(sender=self.__class__, instance=self)
        expr = self.Meta.table.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.Meta.pkname)))
        result = await self.Meta.database.execute(expr)
        self.set_save_status(False)
        await self.signals.post_delete.send(sender=self.__class__, instance=self)
        return result

    async def load(self: T) -> T:
        """
        Allow to refresh existing Models fields from database.
        Be careful as the related models can be overwritten by pk_only models in load.
        Does NOT refresh the related models fields if they were loaded before.

        :raises NoMatch: If given pk is not found in database.

        :return: reloaded Model
        :rtype: Model
        """
        expr = self.Meta.table.select().where(self.pk_column == self.pk)
        row = await self.Meta.database.fetch_one(expr)
        if not row:  # pragma nocover
            raise NoMatch("Instance was deleted from database and cannot be refreshed")
        kwargs = dict(row)
        kwargs = self.translate_aliases_to_columns(kwargs)
        self.update_from_dict(kwargs)
        self.set_save_status(True)
        return self

    async def load_all(
        self: T,
        follow: bool = False,
        exclude: Union[List, str, Set, Dict] = None,
        order_by: Union[List, str] = None,
    ) -> T:
        """
        Allow to refresh existing Models fields from database.
        Performs refresh of the related models fields.

        By default loads only self and the directly related ones.

        If follow=True is set it loads also related models of related models.

        To not get stuck in an infinite loop as related models also keep a relation
        to parent model visited models set is kept.

        That way already visited models that are nested are loaded, but the load do not
        follow them inside. So Model A -> Model B -> Model C -> Model A -> Model X
        will load second Model A but will never follow into Model X.
        Nested relations of those kind need to be loaded manually.

        :param order_by: columns by which models should be sorted
        :type order_by: Union[List, str]
        :raises NoMatch: If given pk is not found in database.

        :param exclude: related models to exclude
        :type exclude: Union[List, str, Set, Dict]
        :param follow: flag to trigger deep save -
        by default only directly related models are saved
        with follow=True also related models of related models are saved
        :type follow: bool
        :return: reloaded Model
        :rtype: Model
        """
        relations = list(self.extract_related_names())
        if follow:
            relations = self._iterate_related_models()
        queryset = self.__class__.objects
        if exclude:
            queryset = queryset.exclude_fields(exclude)
        if order_by:
            queryset = queryset.order_by(order_by)
        instance = await queryset.select_related(relations).get(pk=self.pk)
        self._orm.clear()
        self.update_from_dict(instance.dict())
        return self
