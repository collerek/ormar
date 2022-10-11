from typing import Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from ormar import (
    post_relation_add,
    post_relation_remove,
    pre_relation_add,
    pre_relation_remove,
)
import pydantic
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class AuditLog(ormar.Model):
    class Meta:
        tablename = "audits"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    event_type: str = ormar.String(max_length=100)
    event_log: pydantic.Json = ormar.JSON()


class Cover(ormar.Model):
    class Meta:
        tablename = "covers"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=100)


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id: int = ormar.Integer(name="artist_id", primary_key=True)
    name: str = ormar.String(name="fname", max_length=100)


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=100)
    cover: Optional[Cover] = ormar.ForeignKey(Cover)
    artists = ormar.ManyToMany(Artist)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup():
    yield
    async with database:
        await AuditLog.objects.delete(each=True)


@pytest.mark.asyncio
async def test_relation_signal_functions():
    async with database:
        async with database.transaction(force_rollback=True):

            @pre_relation_add([Album, Cover, Artist])
            async def before_relation_add(
                sender, instance, child, relation_name, passed_kwargs, **kwargs
            ):
                await AuditLog.objects.create(
                    event_type="RELATION_PRE_ADD",
                    event_log=dict(
                        class_affected=sender.get_name(),
                        parent_id=instance.pk,
                        child_id=child.pk,
                        relation_name=relation_name,
                        kwargs=passed_kwargs,
                    ),
                )

                passed_kwargs.pop("dummy", None)

            @post_relation_add([Album, Cover, Artist])
            async def after_relation_add(
                sender, instance, child, relation_name, passed_kwargs, **kwargs
            ):
                await AuditLog.objects.create(
                    event_type="RELATION_POST_ADD",
                    event_log=dict(
                        class_affected=sender.get_name(),
                        parent_id=instance.pk,
                        child_id=child.pk,
                        relation_name=relation_name,
                        kwargs=passed_kwargs,
                    ),
                )

            @pre_relation_remove([Album, Cover, Artist])
            async def before_relation_remove(
                sender, instance, child, relation_name, **kwargs
            ):
                await AuditLog.objects.create(
                    event_type="RELATION_PRE_REMOVE",
                    event_log=dict(
                        class_affected=sender.get_name(),
                        parent_id=instance.pk,
                        child_id=child.pk,
                        relation_name=relation_name,
                        kwargs=kwargs,
                    ),
                )

            @post_relation_remove([Album, Cover, Artist])
            async def after_relation_remove(
                sender, instance, child, relation_name, **kwargs
            ):
                await AuditLog.objects.create(
                    event_type="RELATION_POST_REMOVE",
                    event_log=dict(
                        class_affected=sender.get_name(),
                        parent_id=instance.pk,
                        child_id=child.pk,
                        relation_name=relation_name,
                        kwargs=kwargs,
                    ),
                )

            cover = await Cover(title="New").save()
            artist = await Artist(name="Artist").save()
            album = await Album(title="New Album").save()

            await cover.albums.add(album, index=0)
            log = await AuditLog.objects.get(event_type="RELATION_PRE_ADD")
            assert log.event_log.get("parent_id") == cover.pk
            assert log.event_log.get("child_id") == album.pk
            assert log.event_log.get("relation_name") == "albums"
            assert log.event_log.get("kwargs") == dict(index=0)

            log2 = await AuditLog.objects.get(event_type="RELATION_POST_ADD")
            assert log2.event_log.get("parent_id") == cover.pk
            assert log2.event_log.get("child_id") == album.pk
            assert log2.event_log.get("relation_name") == "albums"
            assert log2.event_log.get("kwargs") == dict(index=0)

            await album.artists.add(artist, dummy="test")

            log3 = await AuditLog.objects.filter(
                event_type="RELATION_PRE_ADD", id__gt=log2.pk
            ).get()
            assert log3.event_log.get("parent_id") == album.pk
            assert log3.event_log.get("child_id") == artist.pk
            assert log3.event_log.get("relation_name") == "artists"
            assert log3.event_log.get("kwargs") == dict(dummy="test")

            log4 = await AuditLog.objects.get(
                event_type="RELATION_POST_ADD", id__gt=log3.pk
            )
            assert log4.event_log.get("parent_id") == album.pk
            assert log4.event_log.get("child_id") == artist.pk
            assert log4.event_log.get("relation_name") == "artists"
            assert log4.event_log.get("kwargs") == dict()

            assert album.cover == cover
            assert len(album.artists) == 1

            await cover.albums.remove(album)
            log = await AuditLog.objects.get(event_type="RELATION_PRE_REMOVE")
            assert log.event_log.get("parent_id") == cover.pk
            assert log.event_log.get("child_id") == album.pk
            assert log.event_log.get("relation_name") == "albums"
            assert log.event_log.get("kwargs") == dict()

            log2 = await AuditLog.objects.get(event_type="RELATION_POST_REMOVE")
            assert log2.event_log.get("parent_id") == cover.pk
            assert log2.event_log.get("child_id") == album.pk
            assert log2.event_log.get("relation_name") == "albums"
            assert log2.event_log.get("kwargs") == dict()

            await album.artists.remove(artist)
            log3 = await AuditLog.objects.filter(
                event_type="RELATION_PRE_REMOVE", id__gt=log2.pk
            ).get()
            assert log3.event_log.get("parent_id") == album.pk
            assert log3.event_log.get("child_id") == artist.pk
            assert log3.event_log.get("relation_name") == "artists"
            assert log3.event_log.get("kwargs") == dict()

            log4 = await AuditLog.objects.get(
                event_type="RELATION_POST_REMOVE", id__gt=log3.pk
            )
            assert log4.event_log.get("parent_id") == album.pk
            assert log4.event_log.get("child_id") == artist.pk
            assert log4.event_log.get("relation_name") == "artists"
            assert log4.event_log.get("kwargs") == dict()

            await album.load_all()
            assert len(album.artists) == 0
            assert album.cover is None
