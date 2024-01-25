from enum import Enum

import databases
import ormar
import sqlalchemy

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
    schema = EnumExample.model_json_schema()
    assert {"MyEnum": {"title": "MyEnum", "enum": [1, 2], "type": "integer"}} == schema[
        "$defs"
    ]
