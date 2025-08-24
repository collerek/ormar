import ormar

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class AutoincrementModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)


class NonAutoincrementModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True, autoincrement=False)


class ExplicitNullableModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True, nullable=True)


create_test_database = init_tests(base_ormar_config)


def test_pk_field_is_not_null():
    for model in [AutoincrementModel, NonAutoincrementModel, ExplicitNullableModel]:
        assert not model.ormar_config.table.c.get("id").nullable
