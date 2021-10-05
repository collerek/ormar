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
async def test_init_and_construct_has_same_effect():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = Company(name="Banzai", hq=hq, founded=1988)
            comp2 = Company.construct(**dict(name="Banzai", hq=hq, founded=1988))
            assert comp.dict() == comp2.dict()
