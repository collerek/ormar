from typing import Optional

import pydantic
import pytest

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
from ormar.exceptions import SignalDefinitionError
from ormar.signals import SignalEmitter
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class AuditLog(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="audits")

    id: int = ormar.Integer(primary_key=True)
    event_type: str = ormar.String(max_length=100)
    event_log: pydantic.Json = ormar.JSON()


class Cover(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="covers")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=100)


class Album(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="albums")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)
    play_count: int = ormar.Integer(default=0)
    cover: Optional[Cover] = ormar.ForeignKey(Cover)


create_test_database = init_tests(base_ormar_config)


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
async def test_signal_functions():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            @pre_save(Album)
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @post_save(Album)
            async def after_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_SAVE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @pre_update(Album)
            async def before_update(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_UPDATE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @post_update(Album)
            async def after_update(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_UPDATE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @pre_delete(Album)
            async def before_delete(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_DELETE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @post_delete(Album)
            async def after_delete(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"POST_DELETE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @post_bulk_update(Album)
            async def after_bulk_update(sender, instances, **kwargs):
                for it in instances:
                    await AuditLog(
                        event_type=f"BULK_POST_UPDATE_{sender.get_name()}",
                        event_log=it.model_dump_json(),
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
async def test_multiple_signals():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            @pre_save(Album)
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            @pre_save(Album)
            async def before_save2(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
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
async def test_static_methods_as_signals():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            class AlbumAuditor:
                event_type = "ALBUM_INSTANCE"

                @staticmethod
                @pre_save(Album)
                async def before_save(sender, instance, **kwargs):
                    await AuditLog(
                        event_type=f"{AlbumAuditor.event_type}_SAVE",
                        event_log=instance.model_dump_json(),
                    ).save()

            album = await Album.objects.create(name="Colorado")
            audits = await AuditLog.objects.all()
            assert len(audits) == 1
            assert audits[0].event_type == "ALBUM_INSTANCE_SAVE"
            assert audits[0].event_log.get("name") == album.name

            album.signals.pre_save.disconnect(AlbumAuditor.before_save)


@pytest.mark.asyncio
async def test_methods_as_signals():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            class AlbumAuditor:
                def __init__(self):
                    self.event_type = "ALBUM_INSTANCE"

                async def before_save(self, sender, instance, **kwargs):
                    await AuditLog(
                        event_type=f"{self.event_type}_SAVE",
                        event_log=instance.model_dump_json(),
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
async def test_multiple_senders_signal():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            @pre_save([Album, Cover])
            async def before_save(sender, instance, **kwargs):
                await AuditLog(
                    event_type=f"PRE_SAVE_{sender.get_name()}",
                    event_log=instance.model_dump_json(),
                ).save()

            cover = await Cover(title="Blue").save()
            album = await Album.objects.create(name="San Francisco", cover=cover)

            audits = await AuditLog.objects.all()
            assert len(audits) == 2
            assert audits[0].event_type == "PRE_SAVE_cover"
            assert audits[0].event_log.get("title") == cover.title
            assert audits[1].event_type == "PRE_SAVE_album"
            assert audits[1].event_log.get("cover") == album.cover.model_dump(
                exclude={"albums"}
            )

            album.signals.pre_save.disconnect(before_save)
            cover.signals.pre_save.disconnect(before_save)


@pytest.mark.asyncio
async def test_modifing_the_instance():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

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
async def test_custom_signal():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):

            async def after_update(sender, instance, **kwargs):
                if instance.play_count > 50 and not instance.is_best_seller:
                    instance.is_best_seller = True
                elif instance.play_count < 50 and instance.is_best_seller:
                    instance.is_best_seller = False
                await instance.update()

            Album.ormar_config.signals.custom.connect(after_update)

            # here album.play_count and is_best_seller get default values
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
            await Album.ormar_config.signals.custom.send(sender=Album, instance=album)
            assert album.is_best_seller

            album.play_count = 30
            await album.update()
            assert album.is_best_seller
            await Album.ormar_config.signals.custom.send(sender=Album, instance=album)
            assert not album.is_best_seller

            Album.ormar_config.signals.custom.disconnect(after_update)
