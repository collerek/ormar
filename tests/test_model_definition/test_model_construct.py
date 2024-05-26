from typing import List

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class NickNames(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")


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
async def test_construct_with_empty_relation():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            await HQ.objects.create(name="Main")
            comp = Company(name="Banzai", hq=None, founded=1988)
            comp2 = Company.model_construct(
                **dict(name="Banzai", hq=None, founded=1988)
            )
            assert comp.model_dump() == comp2.model_dump()


@pytest.mark.asyncio
async def test_init_and_construct_has_same_effect():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = Company(name="Banzai", hq=hq, founded=1988)
            comp2 = Company.model_construct(**dict(name="Banzai", hq=hq, founded=1988))
            assert comp.model_dump() == comp2.model_dump()

            comp3 = Company.model_construct(
                **dict(name="Banzai", hq=hq.model_dump(), founded=1988)
            )
            assert comp.model_dump() == comp3.model_dump()


@pytest.mark.asyncio
async def test_init_and_construct_has_same_effect_with_m2m():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            n1 = await NickNames(name="test").save()
            n2 = await NickNames(name="test2").save()
            hq = HQ(name="Main", nicks=[n1, n2])
            hq2 = HQ.model_construct(**dict(name="Main", nicks=[n1, n2]))
            assert hq.model_dump() == hq2.model_dump()

            hq3 = HQ.model_construct(
                **dict(name="Main", nicks=[n1.model_dump(), n2.model_dump()])
            )
            assert hq.model_dump() == hq3.model_dump()
