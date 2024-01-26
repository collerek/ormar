from typing import Any, Optional, Tuple, Union

import databases
import ormar
import pytest
import sqlalchemy

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="albums",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)
    properties: Tuple[str, Any]
    score: Union[str, int]


class Track(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="tracks",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True, default=0)
    is_disabled: bool = ormar.Boolean(default=False)
    properties: Tuple[str, Any]


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_model_is_replaced_by_a_copy():
    assert Album.model_fields["tracks"].annotation.__args__[1] != Track
    assert (
        Album.model_fields["tracks"].annotation.__args__[1].model_fields.keys()
        == Track.model_fields.keys()
    )
