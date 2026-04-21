import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class FkInhParent(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fk_inh_parents")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class FkInhBase(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: int = ormar.Integer(primary_key=True)
    parent = ormar.ForeignKey(
        FkInhParent,
        related_name="kids",
        foreign_key_name="fk_custom_parent",
    )


class FkInhChildA(FkInhBase):
    ormar_config = base_ormar_config.copy(tablename="fk_inh_child_a")


class FkInhChildB(FkInhBase):
    ormar_config = base_ormar_config.copy(tablename="fk_inh_child_b")


create_test_database = init_tests(base_ormar_config)


def _fk_names(table):
    return [fk.name for col in table.c for fk in col.foreign_keys]


def test_foreign_key_name_is_suffixed_per_subclass_to_avoid_conflicts():
    a_names = _fk_names(FkInhChildA.ormar_config.table)
    b_names = _fk_names(FkInhChildB.ormar_config.table)
    assert "fk_custom_parent_fk_inh_child_a" in a_names
    assert "fk_custom_parent_fk_inh_child_b" in b_names
    assert set(a_names).isdisjoint(set(b_names))
