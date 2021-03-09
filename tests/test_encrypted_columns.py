import uuid
from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100,
                             encrypt_secret='asd123',
                             encrypt_backend=ormar.EncryptBackends.FERNET)
    uuid_test = ormar.UUID(default=uuid.uuid4, uuid_format='string')
    password: str = ormar.String(max_length=100,
                                 encrypt_secret='udxc32',
                                 encrypt_backend=ormar.EncryptBackends.HASH)
    birth_year: int = ormar.Integer(nullable=True,
                                    encrypt_secret='secure89key%^&psdijfipew',
                                    encrypt_max_length=200,
                                    encrypt_backend=ormar.EncryptBackends.FERNET)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_db_structure():
    assert Author.Meta.table.c.get('name').type.impl.__class__ == sqlalchemy.NVARCHAR
    assert Author.Meta.table.c.get('birth_year').type.max_length == 200


@pytest.mark.asyncio
async def test_wrong_query_foreign_key_type():
    async with database:
        await Author(name='Test', birth_year=1988, password='test123').save()
        author = await Author.objects.get()

        assert author.name == 'Test'
        assert author.birth_year == 1988
