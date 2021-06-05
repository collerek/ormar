from typing import Dict, List, TYPE_CHECKING, Tuple, Type

if TYPE_CHECKING:
    from ormar import Model
    from ormar.models.excludable import ExcludableItems


class ReverseAliasResolver:
    def __init__(
        self,
        model_cls: Type["Model"],
        excludable: "ExcludableItems",
        select_related: List[str],
    ) -> None:
        self.select_related = select_related
        self.model_cls = model_cls
        self.reversed_aliases = self.model_cls.Meta.alias_manager.reversed_aliases
        self.excludable = excludable

    def resolve_columns(self, columns_names: List[str]) -> Dict:
        resolved_names = dict()
        prefixes, target_models = self._create_prefixes_map()
        for column_name in columns_names:
            column_parts = column_name.split("_")
            potential_prefix = column_parts[0]
            if potential_prefix in self.reversed_aliases:
                relation = self.reversed_aliases[potential_prefix]
                relation_str = prefixes[relation]
                target_model = target_models[relation]
                allowed_columns = target_model.own_table_columns(
                    model=target_model,
                    excludable=self.excludable,
                    alias=potential_prefix,
                    add_pk_columns=False,
                )
                new_column_name = column_name.replace(f"{potential_prefix}_", "")
                if new_column_name in allowed_columns:
                    resolved_names[column_name] = column_name.replace(
                        f"{potential_prefix}_", f"{relation_str}__"
                    )
            else:
                allowed_columns = self.model_cls.own_table_columns(
                    model=self.model_cls,
                    excludable=self.excludable,
                    add_pk_columns=False,
                )
                if column_name in allowed_columns:
                    resolved_names[column_name] = column_name

        return resolved_names

    def _create_prefixes_map(self) -> Tuple[Dict, Dict]:
        prefixes: Dict = dict()
        target_models: Dict = dict()
        for related in self.select_related:
            model_cls = self.model_cls
            related_split = related.split("__")
            related_str = ""
            for related in related_split:
                prefix_name = f"{model_cls.get_name()}_{related}"
                new_related_str = (f"{related_str}__" if related_str else "") + related
                prefixes[prefix_name] = new_related_str
                field = model_cls.Meta.model_fields[related]
                target_models[prefix_name] = field.to
                if field.is_multi:
                    target_models[prefix_name] = field.through
                    new_through_str = (
                        f"{related_str}__" if related_str else ""
                    ) + field.through.get_name()
                    prefixes[prefix_name] = new_through_str
                    prefix_name = (
                        f"{field.through.get_name()}_"
                        f"{field.default_target_field_name()}"
                    )
                    prefixes[prefix_name] = new_related_str
                    target_models[prefix_name] = field.to
                model_cls = field.to
                related_str = new_related_str
        return prefixes, target_models
