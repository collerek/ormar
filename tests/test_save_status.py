import itertools
from typing import Optional, List

import databases
import pydantic
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class NickNames(ormar.Model):
    class Meta:
        tablename = "nicks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)


class NicksHq(ormar.Model):
    class Meta:
        tablename = "nicks_x_hq"
        metadata = metadata
        database = database


class HQ(ormar.Model):
    class Meta:
        tablename = "hqs"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickNames] = ormar.ManyToMany(NickNames, through=NicksHq)


class Company(ormar.Model):
    class Meta:
        tablename = "companies"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_instantation_false_save_true():
    async with database:
        async with database.transaction(force_rollback=True):
            comp = Company(name='Banzai', founded=1988)
            assert not comp._orm_saved
            await comp.save()
            assert comp._orm_saved


@pytest.mark.asyncio
async def test_saved_edited_not_saved():
    async with database:
        async with database.transaction(force_rollback=True):
            comp = await Company.objects.create(name='Banzai', founded=1988)
            assert comp._orm_saved
            comp.name = 'Banzai2'
            assert not comp._orm_saved

            await comp.update()
            assert comp._orm_saved

            await comp.update(name='Banzai3')
            assert comp._orm_saved

            comp.pk = 999
            assert not comp._orm_saved

            await comp.save()
            assert comp._orm_saved


@pytest.mark.asyncio
async def test_adding_related_gets_dirty():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name='Main')
            comp = await Company.objects.create(name='Banzai', founded=1988)
            assert comp._orm_saved

            comp.hq = hq
            assert not comp._orm_saved
            await comp.update()
            assert comp._orm_saved

            comp = await Company.objects.select_related('hq').get(name='Banzai')
            assert comp._orm_saved
            assert comp.hq.pk == hq.pk
            assert comp.hq._orm_saved


@pytest.mark.asyncio
async def test_adding_many_to_many_does_not_gets_dirty():
    async with database:
        async with database.transaction(force_rollback=True):
            nick1 = await NickNames.objects.create(name='Bazinga', is_lame=False)
            nick2 = await NickNames.objects.create(name='Bazinga2', is_lame=True)

            hq = await HQ.objects.create(name='Main')
            assert hq._orm_saved

            await hq.nicks.add(nick1)
            assert hq._orm_saved
            await hq.nicks.add(nick2)
            assert hq._orm_saved

            hq = await HQ.objects.select_related('nicks').get(name='Main')
            assert hq._orm_saved
            assert hq.nicks[0]._orm_saved

            await hq.nicks.remove(nick1)
            assert hq._orm_saved


@pytest.mark.asyncio
async def test_delete():
    async with database:
        async with database.transaction(force_rollback=True):
            comp = await Company.objects.create(name='Banzai', founded=1988)
            assert comp._orm_saved
            await comp.delete()
            assert not comp._orm_saved

            await comp.save()
            assert comp._orm_saved


@pytest.mark.asyncio
async def test_load():
    async with database:
        async with database.transaction(force_rollback=True):
            comp = await Company.objects.create(name='Banzai', founded=1988)
            assert comp._orm_saved
            comp.name = 'AA'
            assert not comp._orm_saved

            await comp.load()
            assert comp._orm_saved
            assert comp.name == 'Banzai'


@pytest.mark.asyncio
async def test_queryset_methods():
    async with database:
        async with database.transaction(force_rollback=True):
            await Company.objects.create(name='Banzai', founded=1988)
            await Company.objects.create(name='Yuhu', founded=1989)
            await Company.objects.create(name='Konono', founded=1990)
            await Company.objects.create(name='Sumaaa', founded=1991)

            comp = await Company.objects.get(name='Banzai')
            assert comp._orm_saved

            comp = await Company.objects.first()
            assert comp._orm_saved

            comps = await Company.objects.all()
            assert [comp._orm_saved for comp in comps]

            comp2 = await Company.objects.get_or_create(name='Banzai_new', founded=2001)
            assert comp2._orm_saved

            comp3 = await Company.objects.get_or_create(name='Banzai', founded=1988)
            assert comp3._orm_saved
            assert comp3.pk == comp.pk

            update_dict = comp.dict()
            update_dict['founded'] = 2010
            comp = await Company.objects.update_or_create(**update_dict)
            assert comp._orm_saved
            assert comp.founded == 2010

            create_dict = {'name': "Yoko", "founded": 2005}
            comp = await Company.objects.update_or_create(**create_dict)
            assert comp._orm_saved
            assert comp.founded == 2005


@pytest.mark.asyncio
async def test_bulk_methods():
    async with database:
        async with database.transaction(force_rollback=True):
            c1 = Company(name='Banzai', founded=1988)
            c2 = Company(name='Yuhu', founded=1989)

            await Company.objects.bulk_create([c1, c2])
            assert c1._orm_saved
            assert c2._orm_saved

            c1, c2 = await Company.objects.all()
            c1.name = 'Banzai2'
            c2.name = 'Yuhu2'

            assert not c1._orm_saved
            assert not c2._orm_saved

            await Company.objects.bulk_update([c1, c2])
            assert c1._orm_saved
            assert c2._orm_saved
