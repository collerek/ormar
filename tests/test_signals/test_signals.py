from typing import Optional

import databases
import pydantic
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from ormar import (
    post_bulk_update,
    post_delete,
    post_save,
    post_update,
    pre_delete,
    pre_save,
    pre_update,
)
from ormar.signals import SignalEmitter
from ormar.exceptions import SignalDefinitionError
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


class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)
    play_count: int = ormar.Integer(default=0)
    cover: Optional[Cover] = ormar.ForeignKey(Cover)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with database:
        await AuditLog.objects.delete(each=True)


def test_passing_not_callable():
    with pytest.raises(SignalDefinitionError):
        pre_save(Album)("wrong")


def test_passing_callable_without_kwargs():
    with pytest.raises(SignalDefinitionError):

        @pre_save(Album)
        def trigger(sender, instance):  # pragma: no cover
            pass


def test_invalid_signal():
    emitter = SignalEmitter()
    with pytest.raises(SignalDefinitionError):
        emitter.save = 1


@pytest.mark.asyncio
async def test_signal_functions(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            @pre_save(Album)
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @post_save(Album)
            async def after_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_SAVE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @pre_update(Album)
            async def before_update(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_UPDATE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @post_update(Album)
            async def after_update(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_UPDATE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @pre_delete(Album)
            async def before_delete(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_DELETE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @post_delete(Album)
            async def after_delete(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_DELETE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @post_bulk_update(Album)
            async def after_bulk_update(sender, instances, **kwargs):
                for it in instances:
                    await AuditLog(
                        event_type=f"BULK_POST_UPDATE_{sender.get_name()}",
                        event_log=it.json(),
                    ).save()

            album = await Album.objects.create(name="Venice")

            audits = await AuditLog.objects.all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_SAVE_album"
            assert audits[0].event_log.get("name") == album.name
            assert audits[1].event_type == "POST_SAVE_album"
            assert audits[1].event_log.get("id") == album.pk

            album = await Album(name="Rome").save()
            audits = await AuditLog.objects.all()
            assert len(audits) == 4
            assert audits[2].event_type == "PRE_SAVE_album"
            assert audits[2].event_log.get("name") == album.name
            assert audits[3].event_type == "POST_SAVE_album"
            assert audits[3].event_log.get("id") == album.pk

            album.is_best_seller = True
            await album.update()

            audits = await AuditLog.objects.filter(event_type__contains="UPDATE").all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_UPDATE_album"
            assert audits[0].event_log.get("name") == album.name
            assert audits[1].event_type == "POST_UPDATE_album"
            assert audits[1].event_log.get("is_best_seller") == album.is_best_seller

            album.signals.pre_update.disconnect(before_update)
            album.signals.post_update.disconnect(after_update)

            album.is_best_seller = False
            await album.update()

            audits = await AuditLog.objects.filter(event_type__contains="UPDATE").all()
            assert len(audits) == 2

            await album.delete()
            audits = await AuditLog.objects.filter(event_type__contains="DELETE").all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_DELETE_album"
            assert (
                audits[0].event_log.get("id")
                == audits[1].event_log.get("id")
                == album.id
            )
            assert audits[1].event_type == "POST_DELETE_album"

            album.signals.pre_delete.disconnect(before_delete)
            album.signals.post_delete.disconnect(after_delete)
            album.signals.pre_save.disconnect(before_save)
            album.signals.post_save.disconnect(after_save)

            albums = await Album.objects.all()
            assert len(albums)

            for album in albums:
                album.play_count = 1

            await Album.objects.bulk_update(albums)

            cnt = await AuditLog.objects.filter(
                event_type__contains="BULK_POST"
            ).count()
            assert cnt == len(albums)

            album.signals.bulk_post_update.disconnect(after_bulk_update)


@pytest.mark.asyncio
async def test_multiple_signals(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            @pre_save(Album)
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            @pre_save(Album)
            async def before_save2(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            album = await Album.objects.create(name="Miami")
            audits = await AuditLog.objects.all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_SAVE_album"
            assert audits[0].event_log.get("name") == album.name
            assert audits[1].event_type == "PRE_SAVE_album"
            assert audits[1].event_log.get("name") == album.name

            album.signals.pre_save.disconnect(before_save)
            album.signals.pre_save.disconnect(before_save2)


@pytest.mark.asyncio
async def test_static_methods_as_signals(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            class AlbumAuditor:
                event_type = "ALBUM_INSTANCE"

                @staticmethod
                @pre_save(Album)
                async def before_save(sender, instance, **kwargs):
                    await AuditLog(
                        event_type=f"{AlbumAuditor.event_type}_SAVE",
                        event_log=instance.json(),
                    ).save()

            album = await Album.objects.create(name="Colorado")
            audits = await AuditLog.objects.all()
            assert len(audits) == 1
            assert audits[0].event_type == "ALBUM_INSTANCE_SAVE"
            assert audits[0].event_log.get("name") == album.name

            album.signals.pre_save.disconnect(AlbumAuditor.before_save)


@pytest.mark.asyncio
async def test_methods_as_signals(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            class AlbumAuditor:
                def __init__(self):
                    self.event_type = "ALBUM_INSTANCE"

                async def before_save(self, sender, instance, **kwargs):
                    await AuditLog(
                        event_type=f"{self.event_type}_SAVE", event_log=instance.json()
                    ).save()

            auditor = AlbumAuditor()
            pre_save(Album)(auditor.before_save)

            album = await Album.objects.create(name="San Francisco")
            audits = await AuditLog.objects.all()
            assert len(audits) == 1
            assert audits[0].event_type == "ALBUM_INSTANCE_SAVE"
            assert audits[0].event_log.get("name") == album.name

            album.signals.pre_save.disconnect(auditor.before_save)


@pytest.mark.asyncio
async def test_multiple_senders_signal(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            @pre_save([Album, Cover])
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.json(),
                ).save()

            cover = await Cover(title="Blue").save()
            album = await Album.objects.create(name="San Francisco", cover=cover)

            audits = await AuditLog.objects.all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_SAVE_cover"
            assert audits[0].event_log.get("title") == cover.title
            assert audits[1].event_type == "PRE_SAVE_album"
            assert audits[1].event_log.get("cover") == album.cover.dict(
                exclude={"albums"}
            )

            album.signals.pre_save.disconnect(before_save)
            cover.signals.pre_save.disconnect(before_save)


@pytest.mark.asyncio
async def test_modifing_the_instance(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            @pre_update(Album)
            async def before_update(sender, instance, **kwargs):
                if instance.play_count > 50 and not instance.is_best_seller:
                    instance.is_best_seller = True

            # here album.play_count ans is_best_seller get default values
            album = await Album.objects.create(name="Venice")
            assert not album.is_best_seller
            assert album.play_count == 0

            album.play_count = 30
            # here a trigger is called but play_count is too low
            await album.update()
            assert not album.is_best_seller

            album.play_count = 60
            await album.update()
            assert album.is_best_seller
            album.signals.pre_update.disconnect(before_update)


@pytest.mark.asyncio
async def test_custom_signal(cleanup):
    async with database:
        async with database.transaction(force_rollback=True):

            async def after_update(sender, instance, **kwargs):
                if instance.play_count > 50 and not instance.is_best_seller:
                    instance.is_best_seller = True
                elif instance.play_count < 50 and instance.is_best_seller:
                    instance.is_best_seller = False
                await instance.update()

            Album.Meta.signals.custom.connect(after_update)

            # here album.play_count ans is_best_seller get default values
            album = await Album.objects.create(name="Venice")
            assert not album.is_best_seller
            assert album.play_count == 0

            album.play_count = 30
            # here a trigger is called but play_count is too low
            await album.update()
            assert not album.is_best_seller

            album.play_count = 60
            await album.update()
            assert not album.is_best_seller
            await Album.Meta.signals.custom.send(sender=Album, instance=album)
            assert album.is_best_seller

            album.play_count = 30
            await album.update()
            assert album.is_best_seller
            await Album.Meta.signals.custom.send(sender=Album, instance=album)
            assert not album.is_best_seller

            Album.Meta.signals.custom.disconnect(after_update)
