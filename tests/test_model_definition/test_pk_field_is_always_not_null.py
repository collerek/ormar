import databases
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class AutoincrementModel(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)


class NonAutoincrementModel(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True, autoincrement=False)


class ExplicitNullableModel(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True, nullable=True)


def test_pk_field_is_not_null():
    for model in [AutoincrementModel, NonAutoincrementModel, ExplicitNullableModel]:
        assert not model.Meta.table.c.get("id").nullable
