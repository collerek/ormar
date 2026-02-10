from typing import Optional

import ormar
import pytest
import sqlalchemy
from ormar.fields.foreign_key import validate_referential_action

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Artist(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="artists")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Album(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="albums")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    artist: Optional[Artist] = ormar.ForeignKey(Artist, ondelete="CASCADE")


class A(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)


class B(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)
    a: A = ormar.ForeignKey(to=A, ondelete=ormar.ReferentialAction.CASCADE)


class C(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=64, nullalbe=False)
    b: B = ormar.ForeignKey(to=B, ondelete=ormar.ReferentialAction.CASCADE)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_simple_cascade():
    async with base_ormar_config.engine.connect() as conn:
        albums_columns = await conn.run_sync(
            lambda sync_conn: sqlalchemy.inspect(sync_conn).get_columns("albums")
        )
        albums_fks = await conn.run_sync(
            lambda sync_conn: sqlalchemy.inspect(sync_conn).get_foreign_keys("albums")
        )
    assert len(albums_columns) == 3
    col_names = [col.get("name") for col in albums_columns]
    assert sorted(["id", "name", "artist"]) == sorted(col_names)
    assert len(albums_fks) == 1
    assert albums_fks[0]["name"] == "fk_albums_artists_id_artist"
    assert albums_fks[0]["constrained_columns"][0] == "artist"
    assert albums_fks[0]["referred_columns"][0] == "id"
    assert albums_fks[0]["options"].get("ondelete") == "CASCADE"


def test_validations_referential_action():
    CASCADE = ormar.ReferentialAction.CASCADE.value

    assert validate_referential_action(None) is None
    assert validate_referential_action("cascade") == CASCADE
    assert validate_referential_action(ormar.ReferentialAction.CASCADE) == CASCADE

    with pytest.raises(ormar.ModelDefinitionError):
        validate_referential_action("NOT VALID")


@pytest.mark.asyncio
async def test_cascade_clear():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            a = await A.objects.create(name="a")
            b = await B.objects.create(name="b", a=a)
            await C.objects.create(name="c", b=b)

            await a.bs.clear(keep_reversed=False)

            assert await B.objects.count() == 0
            assert await C.objects.count() == 0
