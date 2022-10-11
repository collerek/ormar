# type: ignore
from typing import List

import databases
import pytest
import pytest_asyncio
import sqlalchemy as sa
from pydantic.typing import ForwardRef
from sqlalchemy import create_engine

import ormar
from ormar import ModelMeta
from ormar.exceptions import ModelError
from tests.settings import DATABASE_URL

metadata = sa.MetaData()
db = databases.Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)

PersonRef = ForwardRef("Person")


class Person(ormar.Model):
    class Meta(ModelMeta):
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    supervisor: PersonRef = ormar.ForeignKey(PersonRef, related_name="employees")


Person.update_forward_refs()

GameRef = ForwardRef("Game")
ChildRef = ForwardRef("Child")
ChildFriendRef = ForwardRef("ChildFriend")


class Child(ormar.Model):
    class Meta(ModelMeta):
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    favourite_game: GameRef = ormar.ForeignKey(GameRef, related_name="liked_by")
    least_favourite_game: GameRef = ormar.ForeignKey(
        GameRef, related_name="not_liked_by"
    )
    friends = ormar.ManyToMany(
        ChildRef, through=ChildFriendRef, related_name="also_friends"
    )


class ChildFriend(ormar.Model):
    class Meta(ModelMeta):
        metadata = metadata
        database = db


class Game(ormar.Model):
    class Meta(ModelMeta):
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


Child.update_forward_refs()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with db:
        await ChildFriend.objects.delete(each=True)
        await Child.objects.delete(each=True)
        await Game.objects.delete(each=True)
        await Person.objects.delete(each=True)


@pytest.mark.asyncio
async def test_not_updated_model_raises_errors():
    Person2Ref = ForwardRef("Person2")

    class Person2(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)
        supervisor: Person2Ref = ormar.ForeignKey(Person2Ref, related_name="employees")

    with pytest.raises(ModelError):
        await Person2.objects.create(name="Test")

    with pytest.raises(ModelError):
        Person2(name="Test")

    with pytest.raises(ModelError):
        await Person2.objects.get()


@pytest.mark.asyncio
async def test_not_updated_model_m2m_raises_errors():
    Person3Ref = ForwardRef("Person3")

    class PersonFriend(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

    class Person3(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)
        supervisors: Person3Ref = ormar.ManyToMany(
            Person3Ref, through=PersonFriend, related_name="employees"
        )

    with pytest.raises(ModelError):
        await Person3.objects.create(name="Test")

    with pytest.raises(ModelError):
        Person3(name="Test")

    with pytest.raises(ModelError):
        await Person3.objects.get()


@pytest.mark.asyncio
async def test_not_updated_model_m2m_through_raises_errors():
    PersonPetRef = ForwardRef("PersonPet")

    class Pet(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)

    class Person4(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)
        pets: List[Pet] = ormar.ManyToMany(
            Pet, through=PersonPetRef, related_name="owners"
        )

    class PersonPet(ormar.Model):
        class Meta(ModelMeta):
            metadata = metadata
            database = db

    with pytest.raises(ModelError):
        await Person4.objects.create(name="Test")

    with pytest.raises(ModelError):
        Person4(name="Test")

    with pytest.raises(ModelError):
        await Person4.objects.get()


def test_proper_field_init():
    assert "supervisor" in Person.Meta.model_fields
    assert Person.Meta.model_fields["supervisor"].to == Person

    assert "supervisor" in Person.__fields__
    assert Person.__fields__["supervisor"].type_ == Person

    assert "supervisor" in Person.Meta.table.columns
    assert isinstance(
        Person.Meta.table.columns["supervisor"].type, sa.sql.sqltypes.Integer
    )
    assert len(Person.Meta.table.columns["supervisor"].foreign_keys) > 0

    assert "person_supervisor" in Person.Meta.alias_manager._aliases_new


@pytest.mark.asyncio
async def test_self_relation():
    async with db:
        async with db.transaction(force_rollback=True):
            sam = await Person.objects.create(name="Sam")
            joe = await Person(name="Joe", supervisor=sam).save()
            assert joe.supervisor.name == "Sam"

            joe_check = await Person.objects.select_related("supervisor").get(
                name="Joe"
            )
            assert joe_check.supervisor.name == "Sam"

            sam_check = await Person.objects.select_related("employees").get(name="Sam")
            assert sam_check.name == "Sam"
            assert sam_check.employees[0].name == "Joe"


@pytest.mark.asyncio
async def test_other_forwardref_relation(cleanup):
    async with db:
        async with db.transaction(force_rollback=True):
            checkers = await Game.objects.create(name="checkers")
            uno = await Game(name="Uno").save()

            await Child(
                name="Billy", favourite_game=uno, least_favourite_game=checkers
            ).save()
            await Child(
                name="Kate", favourite_game=checkers, least_favourite_game=uno
            ).save()

            billy_check = await Child.objects.select_related(
                ["favourite_game", "least_favourite_game"]
            ).get(name="Billy")
            assert billy_check.favourite_game == uno
            assert billy_check.least_favourite_game == checkers

            uno_check = await Game.objects.select_related(
                ["liked_by", "not_liked_by"]
            ).get(name="Uno")
            assert uno_check.liked_by[0].name == "Billy"
            assert uno_check.not_liked_by[0].name == "Kate"


@pytest.mark.asyncio
async def test_m2m_self_forwardref_relation(cleanup):
    async with db:
        async with db.transaction(force_rollback=True):
            checkers = await Game.objects.create(name="Checkers")
            uno = await Game(name="Uno").save()
            jenga = await Game(name="Jenga").save()

            billy = await Child(
                name="Billy", favourite_game=uno, least_favourite_game=checkers
            ).save()
            kate = await Child(
                name="Kate", favourite_game=checkers, least_favourite_game=uno
            ).save()
            steve = await Child(
                name="Steve", favourite_game=jenga, least_favourite_game=uno
            ).save()

            await billy.friends.add(kate)
            await billy.friends.add(steve)

            billy_check = await Child.objects.select_related(
                [
                    "friends",
                    "favourite_game",
                    "least_favourite_game",
                    "friends__favourite_game",
                    "friends__least_favourite_game",
                ]
            ).get(name="Billy")
            assert len(billy_check.friends) == 2
            assert billy_check.friends[0].name == "Kate"
            assert billy_check.friends[0].favourite_game.name == "Checkers"
            assert billy_check.friends[0].least_favourite_game.name == "Uno"
            assert billy_check.friends[1].name == "Steve"
            assert billy_check.friends[1].favourite_game.name == "Jenga"
            assert billy_check.friends[1].least_favourite_game.name == "Uno"
            assert billy_check.favourite_game.name == "Uno"

            kate_check = await Child.objects.select_related(["also_friends"]).get(
                name="Kate"
            )

            assert len(kate_check.also_friends) == 1
            assert kate_check.also_friends[0].name == "Billy"

            billy_check = (
                await Child.objects.select_related(
                    [
                        "friends",
                        "favourite_game",
                        "least_favourite_game",
                        "friends__favourite_game",
                        "friends__least_favourite_game",
                    ]
                )
                .filter(friends__favourite_game__name="Checkers")
                .get(name="Billy")
            )
            assert len(billy_check.friends) == 1
            assert billy_check.friends[0].name == "Kate"
            assert billy_check.friends[0].favourite_game.name == "Checkers"
            assert billy_check.friends[0].least_favourite_game.name == "Uno"
