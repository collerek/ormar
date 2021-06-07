from typing import Dict, List, TYPE_CHECKING, Type, cast

if TYPE_CHECKING:  # pragma: no cover
    from ormar import ForeignKeyField, Model
    from ormar.models.excludable import Excludable, ExcludableItems


class ReverseAliasResolver:
    def __init__(
        self,
        model_cls: Type["Model"],
        excludable: "ExcludableItems",
        select_related: List[str],
        exclude_through: bool = False,
    ) -> None:
        self.select_related = select_related
        self.model_cls = model_cls
        self.reversed_aliases = self.model_cls.Meta.alias_manager.reversed_aliases
        self.excludable = excludable
        self.exclude_through = exclude_through

        self._fields: Dict[str, "ForeignKeyField"] = dict()
        self._prefixes: Dict[str, str] = dict()
        self._previous_prefixes: List[str] = [""]
        self._resolved_names: Dict[str, str] = dict()

    def resolve_columns(self, columns_names: List[str]) -> Dict:
        self._create_prefixes_map()
        for column_name in columns_names:
            column_parts = column_name.split("_")
            potential_prefix = column_parts[0]
            if potential_prefix in self.reversed_aliases:
                self._resolve_column_with_prefix(
                    column_name=column_name, prefix=potential_prefix
                )
            else:
                allowed_columns = self.model_cls.own_table_columns(
                    model=self.model_cls,
                    excludable=self.excludable,
                    add_pk_columns=False,
                )
                if column_name in allowed_columns:
                    self._resolved_names[column_name] = column_name

        return self._resolved_names

    def _resolve_column_with_prefix(self, column_name: str, prefix: str) -> None:
        relation = self.reversed_aliases.get(prefix, None)
        relation_str = self._prefixes.get(relation, None)
        field = self._fields.get(relation, None)
        if relation_str is None or field is None:
            return
        is_through = field.is_multi and field.through.get_name() in relation_str
        if self._check_if_field_is_excluded(
            prefix=prefix, field=field, is_through=is_through
        ):
            return

        target_model = field.through if is_through else field.to
        allowed_columns = target_model.own_table_columns(
            model=target_model,
            excludable=self.excludable,
            alias=prefix,
            add_pk_columns=False,
        )
        new_column_name = column_name.replace(f"{prefix}_", "")
        if new_column_name in allowed_columns:
            self._resolved_names[column_name] = column_name.replace(
                f"{prefix}_", f"{relation_str}__"
            )

    def _check_if_field_is_excluded(
        self, prefix: str, field: "ForeignKeyField", is_through: bool
    ) -> bool:
        shift, field_name = 1, field.name
        if is_through:
            field_name = field.through.get_name()
        elif field.is_multi:
            shift = 2
        previous_excludable = self._get_previous_excludable(
            prefix=prefix, field=field, shift=shift
        )
        return previous_excludable.is_excluded(field_name)

    def _get_previous_excludable(
        self, prefix: str, field: "ForeignKeyField", shift: int = 1
    ) -> "Excludable":
        if prefix not in self._previous_prefixes:
            self._previous_prefixes.append(prefix)
        previous_prefix_ind = self._previous_prefixes.index(prefix)
        previous_prefix = (
            self._previous_prefixes[previous_prefix_ind - shift]
            if previous_prefix_ind > (shift - 1)
            else ""
        )
        return self.excludable.get(field.owner, alias=previous_prefix)

    def _create_prefixes_map(self) -> None:
        for related in self.select_related:
            model_cls = self.model_cls
            related_split = related.split("__")
            related_str = ""
            for relation in related_split:
                previous_related_str = f"{related_str}__" if related_str else ""
                new_related_str = previous_related_str + relation
                field = model_cls.Meta.model_fields[relation]
                field = cast("ForeignKeyField", field)
                prefix_name = self._handle_through_fields_and_prefix(
                    model_cls=model_cls,
                    field=field,
                    previous_related_str=previous_related_str,
                    relation=relation,
                )

                self._prefixes[prefix_name] = new_related_str
                self._fields[prefix_name] = field
                model_cls = field.to
                related_str = new_related_str

    def _handle_through_fields_and_prefix(
        self,
        model_cls: Type["Model"],
        field: "ForeignKeyField",
        previous_related_str: str,
        relation: str,
    ) -> str:
        prefix_name = f"{model_cls.get_name()}_{relation}"
        if field.is_multi:
            through_name = field.through.get_name()
            if not self.exclude_through:
                self._fields[prefix_name] = field
                new_through_str = previous_related_str + through_name
                self._prefixes[prefix_name] = new_through_str
            prefix_name = f"{through_name}_{field.default_target_field_name()}"
        return prefix_name
