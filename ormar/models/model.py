from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import sqlalchemy

import ormar.queryset  # noqa I100
from ormar.exceptions import ModelPersistenceError, NoMatch
from ormar.fields.many_to_many import ManyToManyField
from ormar.models import NewBaseModel  # noqa I100
from ormar.models.helpers.models import group_related_list
from ormar.models.metaclass import ModelMeta

if TYPE_CHECKING:  # pragma nocover
    from ormar import QuerySet

T = TypeVar("T", bound="Model")


class Model(NewBaseModel):
    __abstract__ = False
    if TYPE_CHECKING:  # pragma nocover
        Meta: ModelMeta
        objects: "QuerySet"

    def __repr__(self) -> str:  # pragma nocover
        _repr = {k: getattr(self, k) for k, v in self.Meta.model_fields.items()}
        return f"{self.__class__.__name__}({str(_repr)})"

    @classmethod
    def from_row(  # noqa CCR001
        cls: Type[T],
        row: sqlalchemy.engine.ResultProxy,
        select_related: List = None,
        related_models: Any = None,
        previous_model: Type[T] = None,
        source_model: Type[T] = None,
        related_name: str = None,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
        current_relation_str: str = None,
    ) -> Optional[T]:
        """
        Model method to convert raw sql row from database into ormar.Model instance.
        Traverses nested models if they were specified in select_related for query.

        Called recurrently and returns model instance if it's present in the row.
        Note that it's processing one row at a time, so if there are duplicates of
        parent row that needs to be joined/combined
        (like parent row in sql join with 2+ child rows)
        instances populated in this method are later combined in the QuerySet.
        Other method working directly on raw database results is in prefetch_query,
        where rows are populated in a different way as they do not have
        nested models in result.

        :param current_relation_str: name of the relation field
        :type current_relation_str: str
        :param source_model: model on which relation was defined
        :type source_model: Type[Model]
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param select_related: list of names of related models fetched from database
        :type select_related: List
        :param related_models: list or dict of related models
        :type related_models: Union[List, Dict]
        :param previous_model: internal param for nested models to specify table_prefix
        :type previous_model: Model class
        :param related_name: internal parameter - name of current nested model
        :type related_name: str
        :param fields: fields and related model fields to include
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: returns model if model is populated from database
        :rtype: Optional[Model]
        """
        item: Dict[str, Any] = {}
        select_related = select_related or []
        related_models = related_models or []
        table_prefix = ""

        if select_related:
            source_model = cls
            related_models = group_related_list(select_related)

        rel_name2 = related_name

        if (
            previous_model
            and related_name
            and issubclass(
                previous_model.Meta.model_fields[related_name], ManyToManyField
            )
        ):
            through_field = previous_model.Meta.model_fields[related_name]
            if (
                through_field.self_reference
                and related_name == through_field.self_reference_primary
            ):
                rel_name2 = through_field.default_source_field_name()  # type: ignore
            else:
                rel_name2 = through_field.default_target_field_name()  # type: ignore
            previous_model = through_field.through  # type: ignore

        if previous_model and rel_name2:
            if current_relation_str and "__" in current_relation_str and source_model:
                table_prefix = cls.Meta.alias_manager.resolve_relation_alias(
                    from_model=source_model, relation_name=current_relation_str
                )
            if not table_prefix:
                table_prefix = cls.Meta.alias_manager.resolve_relation_alias(
                    from_model=previous_model, relation_name=rel_name2
                )

        item = cls.populate_nested_models_from_row(
            item=item,
            row=row,
            related_models=related_models,
            fields=fields,
            exclude_fields=exclude_fields,
            current_relation_str=current_relation_str,
            source_model=source_model,
        )
        item = cls.extract_prefixed_table_columns(
            item=item,
            row=row,
            table_prefix=table_prefix,
            fields=fields,
            exclude_fields=exclude_fields,
        )

        instance: Optional[T] = None
        if item.get(cls.Meta.pkname, None) is not None:
            item["__excluded__"] = cls.get_names_to_exclude(
                fields=fields, exclude_fields=exclude_fields
            )
            instance = cls(**item)
            instance.set_save_status(True)
        return instance

    @classmethod
    def populate_nested_models_from_row(  # noqa: CFQ002
        cls,
        item: dict,
        row: sqlalchemy.engine.ResultProxy,
        related_models: Any,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
        current_relation_str: str = None,
        source_model: Type[T] = None,
    ) -> dict:
        """
        Traverses structure of related models and populates the nested models
        from the database row.
        Related models can be a list if only directly related models are to be
        populated, converted to dict if related models also have their own related
        models to be populated.

        Recurrently calls from_row method on nested instances and create nested
        instances. In the end those instances are added to the final model dictionary.

        :param source_model: source model from which relation started
        :type source_model: Type[Model]
        :param current_relation_str: joined related parts into one string
        :type current_relation_str: str
        :param item: dictionary of already populated nested models, otherwise empty dict
        :type item: Dict
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param related_models: list or dict of related models
        :type related_models: Union[Dict, List]
        :param fields: fields and related model fields to include -
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """

        for related in related_models:
            relation_str = (
                "__".join([current_relation_str, related])
                if current_relation_str
                else related
            )
            fields = cls.get_included(fields, related)
            exclude_fields = cls.get_excluded(exclude_fields, related)
            model_cls = cls.Meta.model_fields[related].to

            remainder = None
            if isinstance(related_models, dict) and related_models[related]:
                remainder = related_models[related]
            child = model_cls.from_row(
                row,
                related_models=remainder,
                previous_model=cls,
                related_name=related,
                fields=fields,
                exclude_fields=exclude_fields,
                current_relation_str=relation_str,
                source_model=source_model,
            )
            item[model_cls.get_column_name_from_alias(related)] = child

        return item

    @classmethod
    def extract_prefixed_table_columns(  # noqa CCR001
        cls,
        item: dict,
        row: sqlalchemy.engine.result.ResultProxy,
        table_prefix: str,
        fields: Optional[Union[Dict, Set]] = None,
        exclude_fields: Optional[Union[Dict, Set]] = None,
    ) -> dict:
        """
        Extracts own fields from raw sql result, using a given prefix.
        Prefix changes depending on the table's position in a join.

        If the table is a main table, there is no prefix.
        All joined tables have prefixes to allow duplicate column names,
        as well as duplicated joins to the same table from multiple different tables.

        Extracted fields populates the related dict later used to construct a Model.

        Used in Model.from_row and PrefetchQuery._populate_rows methods.

        :param item: dictionary of already populated nested models, otherwise empty dict
        :type item: Dict
        :param row: raw result row from the database
        :type row: sqlalchemy.engine.result.ResultProxy
        :param table_prefix: prefix of the table from AliasManager
        each pair of tables have own prefix (two of them depending on direction) -
        used in joins to allow multiple joins to the same table.
        :type table_prefix: str
        :param fields: fields and related model fields to include -
        if provided only those are included
        :type fields: Optional[Union[Dict, Set]]
        :param exclude_fields: fields and related model fields to exclude
        excludes the fields even if they are provided in fields
        :type exclude_fields: Optional[Union[Dict, Set]]
        :return: dictionary with keys corresponding to model fields names
        and values are database values
        :rtype: Dict
        """
        # databases does not keep aliases in Record for postgres, change to raw row
        source = row._row if cls.db_backend_name() == "postgresql" else row

        selected_columns = cls.own_table_columns(
            model=cls,
            fields=fields or {},
            exclude_fields=exclude_fields or {},
            use_alias=False,
        )

        for column in cls.Meta.table.columns:
            alias = cls.get_column_name_from_alias(column.name)
            if alias not in item and alias in selected_columns:
                prefixed_name = (
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                )
                item[alias] = source[prefixed_name]

        return item

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

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

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
            if self.Meta.model_fields[related].virtual or issubclass(
                self.Meta.model_fields[related], ManyToManyField
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
        rel: T, follow: bool, visited: Set, update_count: int
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

        await self.signals.pre_update.send(sender=self.__class__, instance=self)
        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.get_column_name_from_alias(self.Meta.pkname))
        self_fields = self.translate_columns_to_aliases(self_fields)
        expr = self.Meta.table.update().values(**self_fields)
        expr = expr.where(self.pk_column == getattr(self, self.Meta.pkname))

        await self.Meta.database.execute(expr)
        self.set_save_status(True)
        await self.signals.post_update.send(sender=self.__class__, instance=self)
        return self

    async def delete(self: T) -> int:
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
