# type: ignore
import ormar
import pytest
from pydantic import PydanticUserError, computed_field

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Song(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="songs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    sort_order: int = ormar.Integer()

    @computed_field
    def sorted_name(self) -> str:
        return f"{self.sort_order}: {self.name}"

    @computed_field
    def sample(self) -> str:
        return "sample"

    @computed_field
    def sample2(self) -> str:
        return "sample2"


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_sort_order_on_main_model():
    async with base_ormar_config.database:
        await Song.objects.create(name="Song 3", sort_order=3)
        await Song.objects.create(name="Song 1", sort_order=1)
        await Song.objects.create(name="Song 2", sort_order=2)

        songs = await Song.objects.all()
        song_dict = [song.model_dump() for song in songs]
        assert all("sorted_name" in x for x in song_dict)
        assert all(
            x["sorted_name"] == f"{x['sort_order']}: {x['name']}" for x in song_dict
        )
        song_json = [song.model_dump_json() for song in songs]
        assert all("sorted_name" in x for x in song_json)

        check_include = songs[0].model_dump(include={"sample"})
        assert "sample" in check_include
        assert "sample2" not in check_include
        assert "sorted_name" not in check_include

        check_include = songs[0].model_dump(exclude={"sample"})
        assert "sample" not in check_include
        assert "sample2" in check_include
        assert "sorted_name" in check_include


def test_wrong_definition():
    with pytest.raises(PydanticUserError):

        class WrongModel(ormar.Model):  # pragma: no cover
            @computed_field
            def test(self, aa=10, bb=30):
                pass
