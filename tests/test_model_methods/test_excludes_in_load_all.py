import asyncio
import uuid

import pytest

import ormar
import sqlalchemy
import databases

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta:
    metadata = metadata
    database = database


class JimmyUser(ormar.Model):
    class Meta(BaseMeta):
        tablename = "jimmy_users"

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )


class JimmyProfile(ormar.Model):
    class Meta(BaseMeta):
        tablename = "jimmy_profiles"

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )
    name = ormar.String(max_length=42, default="JimmyProfile")

    user: JimmyUser = ormar.ForeignKey(to=JimmyUser)


class JimmyAccount(ormar.Model):
    class Meta(BaseMeta):
        tablename = "jimmy_accounts"

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )

    name = ormar.String(max_length=42, default="JimmyAccount")

    user: JimmyUser = ormar.ForeignKey(to=JimmyUser)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_excluding_one_relation():
    async with database:
        user = JimmyUser()
        await user.save()

        await JimmyAccount(user=user).save()
        await JimmyProfile(user=user).save()

        await user.load_all(exclude={"jimmyprofiles"})
        assert hasattr(user.jimmyaccounts[0], "name")
        assert len(user.jimmyprofiles) == 0


@pytest.mark.asyncio
async def test_excluding_other_relation():
    async with database:
        user = JimmyUser()
        await user.save()

        await JimmyAccount(user=user).save()
        await JimmyProfile(user=user).save()

        await user.load_all(exclude={"jimmyaccounts"})
        assert await JimmyProfile.objects.get()

        assert hasattr(user.jimmyprofiles[0], "name")
        assert len(user.jimmyaccounts) == 0
