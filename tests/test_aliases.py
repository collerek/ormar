import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Child(ormar.Model):
    class Meta:
        tablename = "children"
        metadata = metadata
        database = database

    id: ormar.Integer(name='child_id', primary_key=True)
    first_name: ormar.String(name='fname', max_length=100)
    last_name: ormar.String(name='lname', max_length=100)
    born_year: ormar.Integer(name='year_born')


class ArtistChildren(ormar.Model):
    class Meta:
        tablename = "children_x_artists"
        metadata = metadata
        database = database


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: ormar.Integer(name='artist_id', primary_key=True)
    first_name: ormar.String(name='fname', max_length=100)
    last_name: ormar.String(name='lname', max_length=100)
    born_year: ormar.Integer(name='year')
    children: ormar.ManyToMany(Child, through=ArtistChildren)


class Album(ormar.Model):
    class Meta:
        tablename = "music_albums"
        metadata = metadata
        database = database

    id: ormar.Integer(name='album_id', primary_key=True)
    name: ormar.String(name='album_name', max_length=100)
    artist: ormar.ForeignKey(Artist, name='artist_id')


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_table_structure():
    assert 'album_id' in [x.name for x in Album.Meta.table.columns]
    assert 'album_name' in [x.name for x in Album.Meta.table.columns]
    assert 'fname' in [x.name for x in Artist.Meta.table.columns]
    assert 'lname' in [x.name for x in Artist.Meta.table.columns]
    assert 'year' in [x.name for x in Artist.Meta.table.columns]


@pytest.mark.asyncio
async def test_working_with_aliases():
    async with database:
        async with database.transaction(force_rollback=True):
            artist = await Artist.objects.create(first_name='Ted', last_name='Mosbey', born_year=1975)
            await Album.objects.create(name="Aunt Robin", artist=artist)

            await artist.children.create(first_name='Son', last_name='1', born_year=1990)
            await artist.children.create(first_name='Son', last_name='2', born_year=1995)

            album = await Album.objects.select_related('artist').first()
            assert album.artist.last_name == 'Mosbey'

            assert album.artist.id is not None
            assert album.artist.first_name == 'Ted'
            assert album.artist.born_year == 1975

            assert album.name == 'Aunt Robin'

            artist = await Artist.objects.select_related('children').get()
            assert len(artist.children) == 2
            assert artist.children[0].first_name == 'Son'
            assert artist.children[1].last_name == '2'

