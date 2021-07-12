import uuid
from typing import List, Optional

import databases
import pytest
import sqlalchemy
from pydantic.typing import ForwardRef

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    email: str = ormar.String(nullable=False, max_length=100)
    role: "Role" = ormar.ForeignKey(
        ForwardRef("Role"),
        nullable=False,
        names={"id": "role_id", "order_no": "role_order_no"},
        name="role_id",
    )


class Role(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "order_no")]

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4)
    order_no: int = ormar.Integer()
    name: str = ormar.String(nullable=False, max_length=100)


User.update_forward_refs()


class Project(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "owner_id")]

    id: int = ormar.Integer()
    owner: User = ormar.ForeignKey(User, name="owner_id")
    name: str = ormar.String(nullable=False, max_length=100)
    tags: Optional[List["Tag"]] = ormar.ManyToMany(ForwardRef("Tag"))


class Tag(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "owner_id")]

    id: int = ormar.Integer()
    owner: User = ormar.ForeignKey(User, name="owner_id")
    name: str = ormar.String(nullable=False, max_length=100)


Project.update_forward_refs()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_forward_ref_in_fk():
    async with database:
        async with database.transaction(force_rollback=True):
            role = await Role(id=uuid.uuid4(), name="Admin", order_no=0).save()
            user = await User(email="test@example.com", role=role).save()

            check = await User.objects.select_related("role").get()
            assert check.email == "test@example.com"
            assert check.pk == user.pk
            assert user.role.name == "Admin"


@pytest.mark.asyncio
async def test_forward_ref_for_m2m():
    async with database:
        async with database.transaction(force_rollback=True):
            role = await Role(id=uuid.uuid4(), name="Admin", order_no=0).save()
            user = await User(email="test@example.com", role=role).save()
            tag = await Tag(id=1, owner=user, name="News").save()
            project = await Project(id=1, name="Test m2m", owner=user).save()

            await project.tags.add(tag)

            check = await Project.objects.select_related(
                [Project.tags.owner, Project.owner.role]
            ).get(name="Test m2m")
            assert check.name == "Test m2m"
            assert check.pk == project.pk
            assert check.tags[0].name == "News"
            assert check.owner.role.name == "Admin"
            assert check.owner.email == "test@example.com"
