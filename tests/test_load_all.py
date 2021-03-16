from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Language(ormar.Model):
    class Meta(BaseMeta):
        tablename = "languages"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    level: str = ormar.String(max_length=150, default="Beginner")


class CringeLevel(ormar.Model):
    class Meta(BaseMeta):
        tablename = "levels"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    language = ormar.ForeignKey(Language)


class NickName(ormar.Model):
    class Meta(BaseMeta):
        tablename = "nicks"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)
    level: Optional[CringeLevel] = ormar.ForeignKey(CringeLevel)


class HQ(ormar.Model):
    class Meta(BaseMeta):
        tablename = "hqs"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickName] = ormar.ManyToMany(NickName)


class Company(ormar.Model):
    class Meta(BaseMeta):
        tablename = "companies"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: Optional[HQ] = ormar.ForeignKey(HQ, related_name="companies")


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_load_all_fk_rel():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            company = await Company.objects.create(name="Banzai", founded=1988, hq=hq)

            hq = await HQ.objects.get(name="Main")
            await hq.load_all()

            assert hq.companies[0] == company
            assert hq.companies[0].name == "Banzai"
            assert hq.companies[0].founded == 1988


@pytest.mark.asyncio
async def test_load_all_many_to_many():
    async with database:
        async with database.transaction(force_rollback=True):
            nick1 = await NickName.objects.create(name="BazingaO", is_lame=False)
            nick2 = await NickName.objects.create(name="Bazinga20", is_lame=True)
            hq = await HQ.objects.create(name="Main")
            await hq.nicks.add(nick1)
            await hq.nicks.add(nick2)

            hq = await HQ.objects.get(name="Main")
            await hq.load_all()

            assert hq.nicks[0] == nick1
            assert hq.nicks[0].name == "BazingaO"

            assert hq.nicks[1] == nick2
            assert hq.nicks[1].name == "Bazinga20"


@pytest.mark.asyncio
async def test_load_all_with_order():
    async with database:
        async with database.transaction(force_rollback=True):
            nick1 = await NickName.objects.create(name="Barry", is_lame=False)
            nick2 = await NickName.objects.create(name="Joe", is_lame=True)
            hq = await HQ.objects.create(name="Main")
            await hq.nicks.add(nick1)
            await hq.nicks.add(nick2)

            hq = await HQ.objects.get(name="Main")
            await hq.load_all(order_by="-nicks__name")

            assert hq.nicks[0] == nick2
            assert hq.nicks[0].name == "Joe"

            assert hq.nicks[1] == nick1
            assert hq.nicks[1].name == "Barry"

            await hq.load_all()
            assert hq.nicks[0] == nick1
            assert hq.nicks[1] == nick2


@pytest.mark.asyncio
async def test_loading_reversed_relation():
    async with database:
        async with database.transaction(force_rollback=True):
            hq = await HQ.objects.create(name="Main")
            await Company.objects.create(name="Banzai", founded=1988, hq=hq)

            company = await Company.objects.get(name="Banzai")
            await company.load_all()

            assert company.hq == hq


@pytest.mark.asyncio
async def test_loading_nested():
    async with database:
        async with database.transaction(force_rollback=True):
            language = await Language.objects.create(name="English")
            level = await CringeLevel.objects.create(name="High", language=language)
            level2 = await CringeLevel.objects.create(name="Low", language=language)
            nick1 = await NickName.objects.create(
                name="BazingaO", is_lame=False, level=level
            )
            nick2 = await NickName.objects.create(
                name="Bazinga20", is_lame=True, level=level2
            )
            hq = await HQ.objects.create(name="Main")
            await hq.nicks.add(nick1)
            await hq.nicks.add(nick2)

            hq = await HQ.objects.get(name="Main")
            await hq.load_all(follow=True)

            assert hq.nicks[0] == nick1
            assert hq.nicks[0].name == "BazingaO"
            assert hq.nicks[0].level.name == "High"
            assert hq.nicks[0].level.language.name == "English"

            assert hq.nicks[1] == nick2
            assert hq.nicks[1].name == "Bazinga20"
            assert hq.nicks[1].level.name == "Low"
            assert hq.nicks[1].level.language.name == "English"

            await hq.load_all(follow=True, exclude="nicks__level__language")
            assert len(hq.nicks) == 2
            assert hq.nicks[0].level.language is None
            assert hq.nicks[1].level.language is None

            await hq.load_all(follow=True, exclude="nicks__level__language__level")
            assert len(hq.nicks) == 2
            assert hq.nicks[0].level.language is not None
            assert hq.nicks[0].level.language.level is None
            assert hq.nicks[1].level.language is not None
            assert hq.nicks[1].level.language.level is None

            await hq.load_all(follow=True, exclude="nicks__level")
            assert len(hq.nicks) == 2
            assert hq.nicks[0].level is None
            assert hq.nicks[1].level is None

            await hq.load_all(follow=True, exclude="nicks")
            assert len(hq.nicks) == 0
