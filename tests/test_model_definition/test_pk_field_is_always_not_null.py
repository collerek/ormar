import databases
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class AutoincrementModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)


class NonAutoincrementModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True, autoincrement=False)


class ExplicitNullableModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True, nullable=True)


def test_pk_field_is_not_null():
    for model in [AutoincrementModel, NonAutoincrementModel, ExplicitNullableModel]:
        assert not model.ormar_config.table.c.get("id").nullable
