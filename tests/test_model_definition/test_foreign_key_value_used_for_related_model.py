import uuid
from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class PageLink(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="pagelinks")

    id: int = ormar.Integer(primary_key=True)
    value: str = ormar.String(max_length=2048)
    country: str = ormar.String(max_length=1000)


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="posts")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=500)
    link: PageLink = ormar.ForeignKey(
        PageLink, related_name="posts", ondelete="CASCADE"
    )


class Department(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4())
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(Department)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_pass_int_values_as_fk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            link = await PageLink(id=1, value="test", country="USA").save()
            await Post.objects.create(title="My post", link=link.id)
            post_check = await Post.objects.select_related("link").get()
            assert post_check.link == link


@pytest.mark.asyncio
async def test_pass_uuid_value_as_fk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            dept = await Department(name="Department test").save()
            await Course(name="Test course", department=dept.id).save()
