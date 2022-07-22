from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from ormar.fields.foreign_key import validate_referential_action
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL)


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, ondelete="CASCADE")


class A(ormar.Model):
    class Meta:
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)


class B(ormar.Model):
    class Meta:
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)
    a: A = ormar.ForeignKey(to=A, ondelete=ormar.ReferentialAction.CASCADE)


class C(ormar.Model):
    class Meta:
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)
    b: B = ormar.ForeignKey(to=B, ondelete=ormar.ReferentialAction.CASCADE)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_simple_cascade():
    inspector = sqlalchemy.inspect(engine)
    columns = inspector.get_columns("albums")
    assert len(columns) == 3
    col_names = [col.get("name") for col in columns]
    assert sorted(["id", "name", "artist"]) == sorted(col_names)
    fks = inspector.get_foreign_keys("albums")
    assert len(fks) == 1
    assert fks[0]["name"] == "fk_albums_artists_id_artist"
    assert fks[0]["constrained_columns"][0] == "artist"
    assert fks[0]["referred_columns"][0] == "id"
    assert fks[0]["options"].get("ondelete") == "CASCADE"


def test_validations_referential_action():
    CASCADE = ormar.ReferentialAction.CASCADE.value

    assert validate_referential_action(None) == None
    assert validate_referential_action("cascade") == CASCADE
    assert validate_referential_action(ormar.ReferentialAction.CASCADE) == CASCADE

    with pytest.raises(ormar.ModelDefinitionError):
        validate_referential_action("NOT VALID")


@pytest.mark.asyncio
async def test_cascade_clear():
    async with database:
        async with database.transaction(force_rollback=True):
            a = await A.objects.create(name="a")
            b = await B.objects.create(name="b", a=a)
            c = await C.objects.create(name="c", b=b)

            await a.bs.clear(keep_reversed=False)

            assert await B.objects.count() == 0
            assert await C.objects.count() == 0
