from typing import List

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class CringeLevel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="levels")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class NickName(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)
    level: CringeLevel = ormar.ForeignKey(CringeLevel)


class NicksHq(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks_x_hq")

    id: int = ormar.Integer(primary_key=True)
    new_field: str = ormar.String(max_length=200, nullable=True)


class HQ(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="hqs")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickName] = ormar.ManyToMany(NickName, through=NicksHq)


class Company(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ, related_name="companies")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_saving_related_reverse_fk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {"companies": [{"name": "Banzai"}], "name": "Main"}
            hq = HQ(**payload)
            count = await hq.save_related(follow=True, save_all=True)
            assert count == 2

            hq_check = await HQ.objects.select_related("companies").get()
            assert hq_check.pk is not None
            assert hq_check.name == "Main"
            assert len(hq_check.companies) == 1
            assert hq_check.companies[0].name == "Banzai"
            assert hq_check.companies[0].pk is not None


@pytest.mark.asyncio
async def test_saving_related_reverse_fk_multiple():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {
                "companies": [{"name": "Banzai"}, {"name": "Yamate"}],
                "name": "Main",
            }
            hq = HQ(**payload)
            count = await hq.save_related(follow=True, save_all=True)
            assert count == 3

            hq_check = await HQ.objects.select_related("companies").get()
            assert hq_check.pk is not None
            assert hq_check.name == "Main"
            assert len(hq_check.companies) == 2
            assert hq_check.companies[0].name == "Banzai"
            assert hq_check.companies[0].pk is not None
            assert hq_check.companies[1].name == "Yamate"
            assert hq_check.companies[1].pk is not None


@pytest.mark.asyncio
async def test_saving_related_fk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {"hq": {"name": "Main"}, "name": "Banzai"}
            comp = Company(**payload)
            count = await comp.save_related(follow=True, save_all=True)
            assert count == 2

            comp_check = await Company.objects.select_related("hq").get()
            assert comp_check.pk is not None
            assert comp_check.name == "Banzai"
            assert comp_check.hq.name == "Main"
            assert comp_check.hq.pk is not None


@pytest.mark.asyncio
async def test_saving_many_to_many_wo_through():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {
                "name": "Main",
                "nicks": [
                    {"name": "Bazinga0", "is_lame": False},
                    {"name": "Bazinga20", "is_lame": True},
                ],
            }

            hq = HQ(**payload)
            count = await hq.save_related()
            assert count == 3

            hq_check = await HQ.objects.select_related("nicks").get()
            assert hq_check.pk is not None
            assert len(hq_check.nicks) == 2
            assert hq_check.nicks[0].name == "Bazinga0"
            assert hq_check.nicks[1].name == "Bazinga20"


@pytest.mark.asyncio
async def test_saving_many_to_many_with_through():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            async with base_ormar_config.database.transaction(force_rollback=True):
                payload = {
                    "name": "Main",
                    "nicks": [
                        {
                            "name": "Bazinga0",
                            "is_lame": False,
                            "nickshq": {"new_field": "test"},
                        },
                        {
                            "name": "Bazinga20",
                            "is_lame": True,
                            "nickshq": {"new_field": "test2"},
                        },
                    ],
                }

                hq = HQ(**payload)
                count = await hq.save_related()
                assert count == 3

                hq_check = await HQ.objects.select_related("nicks").get()
                assert hq_check.pk is not None
                assert len(hq_check.nicks) == 2
                assert hq_check.nicks[0].name == "Bazinga0"
                assert hq_check.nicks[0].nickshq.new_field == "test"
                assert hq_check.nicks[1].name == "Bazinga20"
                assert hq_check.nicks[1].nickshq.new_field == "test2"


@pytest.mark.asyncio
async def test_saving_nested_with_m2m_and_rev_fk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {
                "name": "Main",
                "nicks": [
                    {"name": "Bazinga0", "is_lame": False, "level": {"name": "High"}},
                    {"name": "Bazinga20", "is_lame": True, "level": {"name": "Low"}},
                ],
            }

            hq = HQ(**payload)
            count = await hq.save_related(follow=True, save_all=True)
            assert count == 5

            hq_check = await HQ.objects.select_related("nicks__level").get()
            assert hq_check.pk is not None
            assert len(hq_check.nicks) == 2
            assert hq_check.nicks[0].name == "Bazinga0"
            assert hq_check.nicks[0].level.name == "High"
            assert hq_check.nicks[1].name == "Bazinga20"
            assert hq_check.nicks[1].level.name == "Low"


@pytest.mark.asyncio
async def test_saving_nested_with_m2m_and_rev_fk_and_through():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            payload = {
                "hq": {
                    "name": "Yoko",
                    "nicks": [
                        {
                            "name": "Bazinga0",
                            "is_lame": False,
                            "nickshq": {"new_field": "test"},
                            "level": {"name": "High"},
                        },
                        {
                            "name": "Bazinga20",
                            "is_lame": True,
                            "nickshq": {"new_field": "test2"},
                            "level": {"name": "Low"},
                        },
                    ],
                },
                "name": "Main",
            }

            company = Company(**payload)
            count = await company.save_related(follow=True, save_all=True)
            assert count == 6

            company_check = await Company.objects.select_related(
                "hq__nicks__level"
            ).get()
            assert company_check.pk is not None
            assert company_check.name == "Main"
            assert company_check.hq.name == "Yoko"
            assert len(company_check.hq.nicks) == 2
            assert company_check.hq.nicks[0].name == "Bazinga0"
            assert company_check.hq.nicks[0].nickshq.new_field == "test"
            assert company_check.hq.nicks[0].level.name == "High"
            assert company_check.hq.nicks[1].name == "Bazinga20"
            assert company_check.hq.nicks[1].level.name == "Low"
            assert company_check.hq.nicks[1].nickshq.new_field == "test2"
