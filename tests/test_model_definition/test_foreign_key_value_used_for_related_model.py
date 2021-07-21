import uuid
from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class PageLink(ormar.Model):
    class Meta(BaseMeta):
        tablename = "pagelinks"

    id: int = ormar.Integer(primary_key=True)
    value: str = ormar.String(max_length=2048)
    country: str = ormar.String(max_length=1000)


class Post(ormar.Model):
    class Meta(BaseMeta):
        tablename = "posts"

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=500)
    link: PageLink = ormar.ForeignKey(
        PageLink, related_name="posts", ondelete="CASCADE"
    )


class Department(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4())
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean(default=False)
    department: Optional[Department] = ormar.ForeignKey(Department)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_pass_int_values_as_fk():
    async with database:
        async with database.transaction(force_rollback=True):
            link = await PageLink(id=1, value="test", country="USA").save()
            await Post.objects.create(title="My post", link=link.id)
            post_check = await Post.objects.select_related("link").get()
            assert post_check.link == link


@pytest.mark.asyncio
async def test_pass_uuid_value_as_fk():
    async with database:
        async with database.transaction(force_rollback=True):
            dept = await Department(name="Department test").save()
            await Course(name="Test course", department=dept.id).save()
