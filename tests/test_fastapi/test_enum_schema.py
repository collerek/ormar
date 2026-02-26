from enum import Enum

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class MyEnum(Enum):
    SMALL = 1
    BIG = 2


class EnumExample(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="enum_example")

    id: int = ormar.Integer(primary_key=True)
    size: MyEnum = ormar.Enum(enum_class=MyEnum, default=MyEnum.SMALL)


create_test_database = init_tests(base_ormar_config)


def test_proper_schema():
    schema = EnumExample.model_json_schema()
    assert {"MyEnum": {"title": "MyEnum", "enum": [1, 2], "type": "integer"}} == schema[
        "$defs"
    ]
