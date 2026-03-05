from typing import Any, Optional, Union

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Album(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="albums")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)
    properties: tuple[str, Any]
    score: Union[str, int]


class Track(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tracks")

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: Optional[int] = ormar.Integer(nullable=True, default=0)
    is_disabled: bool = ormar.Boolean(default=False)
    properties: tuple[str, Any]


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_model_is_replaced_by_a_copy():
    assert Album.model_fields["tracks"].annotation.__args__[1] != Track
    assert (
        Album.model_fields["tracks"].annotation.__args__[1].model_fields.keys()
        == Track.model_fields.keys()
    )
