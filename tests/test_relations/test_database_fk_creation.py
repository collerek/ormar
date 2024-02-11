from typing import Optional

import ormar
import pytest
import sqlalchemy
from ormar.fields.foreign_key import validate_referential_action

from tests.settings import create_config
from tests.lifespan import init_tests


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


def test_simple_cascade():
    inspector = sqlalchemy.inspect(base_ormar_config.engine)
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
