import ormar
import pytest
from ormar.models import Model

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Comment(Model):
    ormar_config = base_ormar_config.copy(tablename="comments")

    test: int = ormar.Integer(primary_key=True, comment="primary key of comments")
    test_string: str = ormar.String(max_length=250, comment="test that it works")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_comments_are_set_in_db():
    columns = Comment.ormar_config.table.c
    for c in columns:
        assert c.comment == Comment.ormar_config.model_fields[c.name].comment
