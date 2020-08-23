from typing import List, TYPE_CHECKING, Type

from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


class RelationshipCrawler:
    def __init__(self) -> None:
        self._select_related = []
        self.auto_related = []
        self.already_checked = []

    def discover_relations(
        self, select_related: List, prev_model: Type["Model"]
    ) -> List[str]:
        self._select_related = select_related
        self._extract_auto_required_relations(prev_model=prev_model)
        self._include_auto_related_models()
        return self._select_related

    @staticmethod
    def _field_is_a_foreign_key_and_no_circular_reference(
        field: Type[BaseField], field_name: str, rel_part: str
    ) -> bool:
        return issubclass(field, ForeignKeyField) and field_name not in rel_part

    def _field_qualifies_to_deeper_search(
        self, field: ForeignKeyField, parent_virtual: bool, nested: bool, rel_part: str
    ) -> bool:
        prev_part_of_related = "__".join(rel_part.split("__")[:-1])
        partial_match = any(
            [x.startswith(prev_part_of_related) for x in self._select_related]
        )
        already_checked = any(
            [x.startswith(rel_part) for x in (self.auto_related + self.already_checked)]
        )
        return (
            (field.virtual and parent_virtual)
            or (partial_match and not already_checked)
        ) or not nested

    def _extract_auto_required_relations(
        self,
        prev_model: Type["Model"],
        rel_part: str = "",
        nested: bool = False,
        parent_virtual: bool = False,
    ) -> None:
        for field_name, field in prev_model.Meta.model_fields.items():
            if self._field_is_a_foreign_key_and_no_circular_reference(
                field, field_name, rel_part
            ):
                rel_part = field_name if not rel_part else rel_part + "__" + field_name
                if not field.nullable:
                    if rel_part not in self._select_related:
                        split_tables = rel_part.split("__")
                        new_related = (
                            "__".join(split_tables[:-1])
                            if len(split_tables) > 1
                            else rel_part
                        )
                        self.auto_related.append(new_related)
                    rel_part = ""
                elif self._field_qualifies_to_deeper_search(
                    field, parent_virtual, nested, rel_part
                ):

                    self._extract_auto_required_relations(
                        prev_model=field.to,
                        rel_part=rel_part,
                        nested=True,
                        parent_virtual=field.virtual,
                    )
                else:
                    self.already_checked.append(rel_part)
                    rel_part = ""

    def _include_auto_related_models(self) -> None:
        if self.auto_related:
            new_joins = []
            for join in self._select_related:
                if not any([x.startswith(join) for x in self.auto_related]):
                    new_joins.append(join)
            self._select_related = new_joins + self.auto_related
