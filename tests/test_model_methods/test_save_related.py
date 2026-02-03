from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class CringeLevel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="levels")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class NickName(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: Optional[bool] = ormar.Boolean(nullable=True)
    level: CringeLevel = ormar.ForeignKey(CringeLevel)


class NicksHq(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks_x_hq")


class HQ(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="hqs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: list[NickName] = ormar.ManyToMany(NickName, through=NicksHq)


class Company(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: Optional[int] = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ, related_name="companies")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_saving_related_fk_rel():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            comp = await Company.objects.create(name="Banzai", founded=1988, hq=hq)
            assert comp.saved

            count = await comp.save_related()
            assert count == 0

            comp.hq.name = "Suburbs"
            assert not comp.hq.saved
            assert comp.saved

            count = await comp.save_related()
            assert count == 1
            assert comp.hq.saved

            comp.hq.name = "Suburbs 2"
            assert not comp.hq.saved
            assert comp.saved

            count = await comp.save_related(exclude={"hq"})
            assert count == 0
            assert not comp.hq.saved


@pytest.mark.asyncio
async def test_saving_many_to_many():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            nick1 = await NickName.objects.create(name="BazingaO", is_lame=False)
            nick2 = await NickName.objects.create(name="Bazinga20", is_lame=True)

            hq = await HQ.objects.create(name="Main")
            assert hq.saved

            await hq.nicks.add(nick1)
            assert hq.saved
            await hq.nicks.add(nick2)
            assert hq.saved

            count = await hq.save_related()
            assert count == 0

            count = await hq.save_related(save_all=True)
            assert count == 3

            hq.nicks[0].name = "Kabucha"
            hq.nicks[1].name = "Kabucha2"
            assert not hq.nicks[0].saved
            assert not hq.nicks[1].saved

            count = await hq.save_related()
            assert count == 2
            assert hq.nicks[0].saved
            assert hq.nicks[1].saved

            hq.nicks[0].name = "Kabucha a"
            hq.nicks[1].name = "Kabucha2 a"
            assert not hq.nicks[0].saved
            assert not hq.nicks[1].saved

            count = await hq.save_related(exclude={"nicks": ...})
            assert count == 0
            assert not hq.nicks[0].saved
            assert not hq.nicks[1].saved


@pytest.mark.asyncio
async def test_saving_reversed_relation():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            await Company.objects.create(name="Banzai", founded=1988, hq=hq)

            hq = await HQ.objects.select_related("companies").get(name="Main")
            assert hq.saved
            assert hq.companies[0].saved

            hq.companies[0].name = "Konichiwa"
            assert not hq.companies[0].saved
            count = await hq.save_related()
            assert count == 1
            assert hq.companies[0].saved

            await Company.objects.create(name="Joshua", founded=1888, hq=hq)

            hq = await HQ.objects.select_related("companies").get(name="Main")
            assert hq.saved
            assert hq.companies[0].saved
            assert hq.companies[1].saved

            hq.companies[0].name = hq.companies[0].name + "20"
            assert not hq.companies[0].saved
            # save only if not saved so now only one
            count = await hq.save_related()
            assert count == 1
            assert hq.companies[0].saved

            hq.companies[0].name = hq.companies[0].name + "20"
            hq.companies[1].name = hq.companies[1].name + "30"
            assert not hq.companies[0].saved
            assert not hq.companies[1].saved
            count = await hq.save_related()
            assert count == 2
            assert hq.companies[0].saved
            assert hq.companies[1].saved


@pytest.mark.asyncio
async def test_saving_nested():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            level = await CringeLevel.objects.create(name="High")
            level2 = await CringeLevel.objects.create(name="Low")
            nick1 = await NickName.objects.create(
                name="BazingaO", is_lame=False, level=level
            )
            nick2 = await NickName.objects.create(
                name="Bazinga20", is_lame=True, level=level2
            )

            hq = await HQ.objects.create(name="Main")
            assert hq.saved

            await hq.nicks.add(nick1)
            assert hq.saved
            await hq.nicks.add(nick2)
            assert hq.saved

            count = await hq.save_related()
            assert count == 0

            hq.nicks[0].level.name = "Medium"
            assert not hq.nicks[0].level.saved
            assert hq.nicks[0].saved

            count = await hq.save_related(follow=True)
            assert count == 1
            assert hq.nicks[0].saved
            assert hq.nicks[0].level.saved

            hq.nicks[0].level.name = "Low"
            hq.nicks[1].level.name = "Medium"
            assert not hq.nicks[0].level.saved
            assert not hq.nicks[1].level.saved
            assert hq.nicks[0].saved
            assert hq.nicks[1].saved

            count = await hq.save_related(follow=True)
            assert count == 2
            assert hq.nicks[0].saved
            assert hq.nicks[0].level.saved
            assert hq.nicks[1].saved
            assert hq.nicks[1].level.saved

            hq.nicks[0].level.name = "Low 2"
            hq.nicks[1].level.name = "Medium 2"
            assert not hq.nicks[0].level.saved
            assert not hq.nicks[1].level.saved
            assert hq.nicks[0].saved
            assert hq.nicks[1].saved
            count = await hq.save_related(follow=True, exclude={"nicks": {"level"}})
            assert count == 0
            assert hq.nicks[0].saved
            assert not hq.nicks[0].level.saved
            assert hq.nicks[1].saved
            assert not hq.nicks[1].level.saved
