import uuid

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config(force_rollback=True)


class JimmyUser(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="jimmy_users")

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )


class JimmyProfile(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="jimmy_profiles")

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )
    name = ormar.String(max_length=42, default="JimmyProfile")
    user: JimmyUser = ormar.ForeignKey(to=JimmyUser)


class JimmyAccount(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="jimmy_accounts")

    id: uuid.UUID = ormar.UUID(
        primary_key=True, default=uuid.uuid4(), uuid_format="string"
    )
    name = ormar.String(max_length=42, default="JimmyAccount")
    user: JimmyUser = ormar.ForeignKey(to=JimmyUser)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_excluding_one_relation():
    async with base_ormar_config.database:
        user = JimmyUser()
        await user.save()

        await JimmyAccount(user=user).save()
        await JimmyProfile(user=user).save()

        await user.load_all(exclude={"jimmyprofiles"})
        assert hasattr(user.jimmyaccounts[0], "name")
        assert len(user.jimmyprofiles) == 0


@pytest.mark.asyncio
async def test_excluding_other_relation():
    async with base_ormar_config.database:
        user = JimmyUser()
        await user.save()

        await JimmyAccount(user=user).save()
        await JimmyProfile(user=user).save()

        await user.load_all(exclude={"jimmyaccounts"})
        assert await JimmyProfile.objects.get()

        assert hasattr(user.jimmyprofiles[0], "name")
        assert len(user.jimmyaccounts) == 0
