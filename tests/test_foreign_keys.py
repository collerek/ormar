import databases
import pytest
import sqlalchemy
from pydantic import ValidationError

import ormar
from ormar.exceptions import NoMatch, MultipleMatches, RelationshipInstanceError
from ormar.fields.foreign_key import ForeignKeyField
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    album: ormar.ForeignKey(Album)
    title: ormar.String(max_length=100)
    position: ormar.Integer()


class Cover(ormar.Model):
    class Meta:
        tablename = "covers"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    album: ormar.ForeignKey(Album, related_name="cover_pictures")
    title: ormar.String(max_length=100)


class Organisation(ormar.Model):
    class Meta:
        tablename = "org"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    ident: ormar.String(max_length=100)


class Team(ormar.Model):
    class Meta:
        tablename = "teams"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    org: ormar.ForeignKey(Organisation)
    name: ormar.String(max_length=100)


class Member(ormar.Model):
    class Meta:
        tablename = "members"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    team: ormar.ForeignKey(Team)
    email: ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_wrong_query_foreign_key_type():
    with pytest.raises(RelationshipInstanceError):
        Track(title="The Error", album="wrong_pk_type")


@pytest.mark.asyncio
async def test_setting_explicitly_empty_relation():
    async with database:
        track = Track(album=None, title="The Bird", position=1)
        assert track.album is None


@pytest.mark.asyncio
async def test_related_name():
    async with database:
        album = await Album.objects.create(name="Vanilla")
        await Cover.objects.create(album=album, title="The cover file")

        assert len(album.cover_pictures) == 1


@pytest.mark.asyncio
async def test_model_crud():
    async with database:
        album = Album(name="Malibu")
        await album.save()
        track1 = Track(album=album, title="The Bird", position=1)
        track2 = Track(album=album, title="Heart don't stand a chance", position=2)
        track3 = Track(album=album, title="The Waters", position=3)
        await track1.save()
        await track2.save()
        await track3.save()

        track = await Track.objects.get(title="The Bird")
        assert track.album.pk == album.pk
        assert isinstance(track.album, ormar.Model)
        assert track.album.name is None
        await track.album.load()
        assert track.album.name == "Malibu"

        assert len(album.tracks) == 3
        assert album.tracks[1].title == "Heart don't stand a chance"

        album1 = await Album.objects.get(name="Malibu")
        assert album1.pk == 1
        assert album1.tracks == []

        await Track.objects.create(album={"id": track.album.pk}, title="The Bird2", position=4)


@pytest.mark.asyncio
async def test_select_related():
    async with database:
        album = Album(name="Malibu")
        await album.save()
        track1 = Track(album=album, title="The Bird", position=1)
        track2 = Track(album=album, title="Heart don't stand a chance", position=2)
        track3 = Track(album=album, title="The Waters", position=3)
        await track1.save()
        await track2.save()
        await track3.save()

        fantasies = Album(name="Fantasies")
        await fantasies.save()
        track4 = Track(album=fantasies, title="Help I'm Alive", position=1)
        track5 = Track(album=fantasies, title="Sick Muse", position=2)
        track6 = Track(album=fantasies, title="Satellite Mind", position=3)
        await track4.save()
        await track5.save()
        await track6.save()

        track = await Track.objects.select_related("album").get(title="The Bird")
        assert track.album.name == "Malibu"

        tracks = await Track.objects.select_related("album").all()
        assert len(tracks) == 6


@pytest.mark.asyncio
async def test_fk_filter():
    async with database:
        malibu = Album(name="Malibu%")
        await malibu.save()
        await Track.objects.create(album=malibu, title="The Bird", position=1)
        await Track.objects.create(
            album=malibu, title="Heart don't stand a chance", position=2
        )
        await Track.objects.create(album=malibu, title="The Waters", position=3)

        fantasies = await Album.objects.create(name="Fantasies")
        await Track.objects.create(album=fantasies, title="Help I'm Alive", position=1)
        await Track.objects.create(album=fantasies, title="Sick Muse", position=2)
        await Track.objects.create(album=fantasies, title="Satellite Mind", position=3)

        tracks = (
            await Track.objects.select_related("album")
                .filter(album__name="Fantasies")
                .all()
        )
        assert len(tracks) == 3
        for track in tracks:
            assert track.album.name == "Fantasies"

        tracks = (
            await Track.objects.select_related("album")
                .filter(album__name__icontains="fan")
                .all()
        )
        assert len(tracks) == 3
        for track in tracks:
            assert track.album.name == "Fantasies"

        tracks = await Track.objects.filter(album__name__contains="fan").all()
        assert len(tracks) == 3
        for track in tracks:
            assert track.album.name == "Fantasies"

        tracks = await Track.objects.filter(album__name__contains="Malibu%").all()
        assert len(tracks) == 3

        tracks = await Track.objects.filter(album=malibu).select_related("album").all()
        assert len(tracks) == 3
        for track in tracks:
            assert track.album.name == "Malibu%"

        tracks = await Track.objects.select_related("album").all(album=malibu)
        assert len(tracks) == 3
        for track in tracks:
            assert track.album.name == "Malibu%"


@pytest.mark.asyncio
async def test_multiple_fk():
    async with database:
        acme = await Organisation.objects.create(ident="ACME Ltd")
        red_team = await Team.objects.create(org=acme, name="Red Team")
        blue_team = await Team.objects.create(org=acme, name="Blue Team")
        await Member.objects.create(team=red_team, email="a@example.org")
        await Member.objects.create(team=red_team, email="b@example.org")
        await Member.objects.create(team=blue_team, email="c@example.org")
        await Member.objects.create(team=blue_team, email="d@example.org")

        other = await Organisation.objects.create(ident="Other ltd")
        team = await Team.objects.create(org=other, name="Green Team")
        await Member.objects.create(team=team, email="e@example.org")

        members = (
            await Member.objects.select_related("team__org")
                .filter(team__org__ident="ACME Ltd")
                .all()
        )
        assert len(members) == 4
        for member in members:
            assert member.team.org.ident == "ACME Ltd"


@pytest.mark.asyncio
async def test_pk_filter():
    async with database:
        fantasies = await Album.objects.create(name="Test")
        await Track.objects.create(album=fantasies, title="Test1", position=1)
        await Track.objects.create(album=fantasies, title="Test2", position=2)
        await Track.objects.create(album=fantasies, title="Test3", position=3)
        tracks = await Track.objects.select_related("album").filter(pk=1).all()
        assert len(tracks) == 1

        tracks = (
            await Track.objects.select_related("album")
                .filter(position=2, album__name="Test")
                .all()
        )
        assert len(tracks) == 1


@pytest.mark.asyncio
async def test_limit_and_offset():
    async with database:
        fantasies = await Album.objects.create(name="Limitless")
        await Track.objects.create(id=None, album=fantasies, title="Sample", position=1)
        await Track.objects.create(album=fantasies, title="Sample2", position=2)
        await Track.objects.create(album=fantasies, title="Sample3", position=3)

        tracks = await Track.objects.limit(1).all()
        assert len(tracks) == 1
        assert tracks[0].title == "Sample"

        tracks = await Track.objects.limit(1).offset(1).all()
        assert len(tracks) == 1
        assert tracks[0].title == "Sample2"


@pytest.mark.asyncio
async def test_get_exceptions():
    async with database:
        fantasies = await Album.objects.create(name="Test")

        with pytest.raises(NoMatch):
            await Album.objects.get(name="Test2")

        await Track.objects.create(album=fantasies, title="Test1", position=1)
        await Track.objects.create(album=fantasies, title="Test2", position=2)
        await Track.objects.create(album=fantasies, title="Test3", position=3)
        with pytest.raises(MultipleMatches):
            await Track.objects.select_related("album").get(album=fantasies)


@pytest.mark.asyncio
async def test_wrong_model_passed_as_fk():
    with pytest.raises(RelationshipInstanceError):
        org = await Organisation.objects.create(ident="ACME Ltd")
        await Track.objects.create(album=org, title="Test1", position=1)
