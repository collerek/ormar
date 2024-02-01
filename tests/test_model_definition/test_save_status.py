from typing import List

import ormar
import pytest
from ormar.exceptions import ModelPersistenceError

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class NickNames(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)


class NicksHq(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks_x_hq")


class HQ(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="hqs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickNames] = ormar.ManyToMany(NickNames, through=NicksHq)


class Company(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_instantiation_false_save_true():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            comp = Company(name="Banzai", founded=1988)
            assert not comp.saved
            await comp.save()
            assert comp.saved


@pytest.mark.asyncio
async def test_saved_edited_not_saved():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            comp = await Company.objects.create(name="Banzai", founded=1988)
            assert comp.saved
            comp.name = "Banzai2"
            assert not comp.saved

            await comp.update()
            assert comp.saved

            await comp.update(name="Banzai3")
            assert comp.saved

            comp.pk = 999
            assert not comp.saved

            await comp.update()
            assert comp.saved


@pytest.mark.asyncio
async def test_adding_related_gets_dirty():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = await Company.objects.create(name="Banzai", founded=1988)
            assert comp.saved

            comp.hq = hq
            assert not comp.saved
            await comp.update()
            assert comp.saved

            comp = await Company.objects.select_related("hq").get(name="Banzai")
            assert comp.saved

            assert comp.hq.pk == hq.pk
            assert comp.hq.saved

            comp.hq.name = "Suburbs"
            assert not comp.hq.saved
            assert comp.saved

            await comp.hq.update()
            assert comp.hq.saved


@pytest.mark.asyncio
async def test_adding_many_to_many_does_not_gets_dirty():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            nick1 = await NickNames.objects.create(name="Bazinga", is_lame=False)
            nick2 = await NickNames.objects.create(name="Bazinga2", is_lame=True)

            hq = await HQ.objects.create(name="Main")
            assert hq.saved

            await hq.nicks.add(nick1)
            assert hq.saved
            await hq.nicks.add(nick2)
            assert hq.saved

            hq = await HQ.objects.select_related("nicks").get(name="Main")
            assert hq.saved
            assert hq.nicks[0].saved

            await hq.nicks.remove(nick1)
            assert hq.saved

            hq.nicks[0].name = "Kabucha"
            assert not hq.nicks[0].saved

            await hq.nicks[0].update()
            assert hq.nicks[0].saved


@pytest.mark.asyncio
async def test_delete():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            comp = await Company.objects.create(name="Banzai", founded=1988)
            assert comp.saved
            await comp.delete()
            assert not comp.saved

            await comp.update()
            assert comp.saved


@pytest.mark.asyncio
async def test_load():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            comp = await Company.objects.create(name="Banzai", founded=1988)
            assert comp.saved
            comp.name = "AA"
            assert not comp.saved

            await comp.load()
            assert comp.saved
            assert comp.name == "Banzai"


@pytest.mark.asyncio
async def test_queryset_methods():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await Company.objects.create(name="Banzai", founded=1988)
            await Company.objects.create(name="Yuhu", founded=1989)
            await Company.objects.create(name="Konono", founded=1990)
            await Company.objects.create(name="Sumaaa", founded=1991)

            comp = await Company.objects.get(name="Banzai")
            assert comp.saved

            comp = await Company.objects.first()
            assert comp.saved

            comps = await Company.objects.all()
            assert [comp.saved for comp in comps]

            comp2, created = await Company.objects.get_or_create(
                name="Banzai_new", founded=2001
            )
            assert comp2.saved
            assert created is True

            comp3, created = await Company.objects.get_or_create(
                name="Banzai", founded=1988
            )
            assert comp3.saved
            assert comp3.pk == comp.pk
            assert created is False

            update_dict = comp.model_dump()
            update_dict["founded"] = 2010
            comp = await Company.objects.update_or_create(**update_dict)
            assert comp.saved
            assert comp.founded == 2010

            create_dict = {"name": "Yoko", "founded": 2005}
            comp = await Company.objects.update_or_create(**create_dict)
            assert comp.saved
            assert comp.founded == 2005


@pytest.mark.asyncio
async def test_bulk_methods():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            c1 = Company(name="Banzai", founded=1988)
            c2 = Company(name="Yuhu", founded=1989)

            await Company.objects.bulk_create([c1, c2])
            assert c1.saved
            assert c2.saved

            c1, c2 = await Company.objects.all()
            c1.name = "Banzai2"
            c2.name = "Yuhu2"

            assert not c1.saved
            assert not c2.saved

            await Company.objects.bulk_update([c1, c2])
            assert c1.saved
            assert c2.saved

            c3 = Company(name="Cobra", founded=2088)
            assert not c3.saved

            with pytest.raises(ModelPersistenceError):
                await c3.update()

            await c3.upsert()
            assert c3.saved

            c3.name = "Python"
            assert not c3.saved

            await c3.upsert()
            assert c3.saved
            assert c3.name == "Python"

            await c3.upsert(founded=2077)
            assert c3.saved
            assert c3.founded == 2077
