from typing import List

import databases
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
async def test_construct_with_empty_relation():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = Company(name="Banzai", hq=None, founded=1988)
            comp2 = Company.construct(**dict(name="Banzai", hq=None, founded=1988))
            assert comp.dict() == comp2.dict()


@pytest.mark.asyncio
async def test_init_and_construct_has_same_effect():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = Company(name="Banzai", hq=hq, founded=1988)
            comp2 = Company.construct(**dict(name="Banzai", hq=hq, founded=1988))
            assert comp.dict() == comp2.dict()

            comp3 = Company.construct(**dict(name="Banzai", hq=hq.dict(), founded=1988))
            assert comp.dict() == comp3.dict()


@pytest.mark.asyncio
async def test_init_and_construct_has_same_effect_with_m2m():
    async with database:
        async with database.transaction(force_rollback=True):
            n1 = await NickNames(name="test").save()
            n2 = await NickNames(name="test2").save()
            hq = HQ(name="Main", nicks=[n1, n2])
            hq2 = HQ.construct(**dict(name="Main", nicks=[n1, n2]))
            assert hq.dict() == hq2.dict()

            hq3 = HQ.construct(**dict(name="Main", nicks=[n1.dict(), n2.dict()]))
            assert hq.dict() == hq3.dict()
