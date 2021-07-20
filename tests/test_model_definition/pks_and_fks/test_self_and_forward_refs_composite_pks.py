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


class Employee(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "phone")]

    id: int = ormar.Integer()
    phone: str = ormar.String(max_length=30)
    name: str = ormar.String(nullable=False, max_length=100)
    manager: Optional["Employee"] = ormar.ForeignKey(
        ForwardRef("Employee"), related_name="team_members"
    )
    supervisors: Optional[List["Employee"]] = ormar.ManyToMany(ForwardRef("Employee"))


Employee.update_forward_refs()


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


@pytest.mark.asyncio
async def test_self_refs():
    async with database:
        async with database.transaction(force_rollback=True):
            john = await Employee(name="John", id=1, phone="123456789").save()
            sam = await Employee(
                name="Sam", id=2, phone="123456788", manager=john
            ).save()
            sue = await Employee(
                name="Sue", id=3, phone="123456787", manager=john
            ).save()
            await sam.supervisors.add(sue)

            check = (
                await Employee.objects.select_related(Employee.manager)
                .prefetch_related(Employee.supervisors)
                .get(id=2, phone="123456788")
            )
            assert check.name == "Sam"
            assert check.supervisors[0] == sue
            assert check.manager == john

            check2 = (
                await Employee.objects.select_related(Employee.manager)
                .prefetch_related(Employee.employees)
                .get(id=3, phone="123456787")
            )
            assert check2.name == "Sue"
            assert check2.employees[0] == sam
            assert check2.manager == john

            check3 = await Employee.objects.prefetch_related(
                [Employee.manager, Employee.employees]
            ).get(id=3, phone="123456787")
            assert check3.name == "Sue"
            assert check3.employees[0] == sam
            assert check3.manager == john
