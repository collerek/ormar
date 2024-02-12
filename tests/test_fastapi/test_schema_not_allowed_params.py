import databases
import ormar
import sqlalchemy

from tests.lifespan import init_tests
from tests.settings import create_config


base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    contents: str = ormar.Text()


create_test_database = init_tests(base_ormar_config)


def test_schema_not_allowed():
    schema = Author.model_json_schema()
    for field_schema in schema.get("properties").values():
        for key in field_schema.keys():
            assert "_" not in key, f"Found illegal field in openapi schema: {key}"
