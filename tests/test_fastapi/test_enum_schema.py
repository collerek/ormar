from enum import Enum

import databases
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class MyEnum(Enum):
    SMALL = 1
    BIG = 2


class EnumExample(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="enum_example",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


def test_proper_schema():
    schema = EnumExample.schema_json()
    assert '{"MyEnum": {"title": "MyEnum", "description": "An enumeration.", ' '"enum": [1, 2]}}' in schema
