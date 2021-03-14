from typing import Any, Dict, List, Type
from uuid import UUID, uuid4

import databases
import pytest
import sqlalchemy

import ormar
from ormar import ModelDefinitionError, Model, QuerySet, pre_update
from ormar import pre_save, pre_relation_add
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Animal(ormar.Model):
    class Meta(BaseMeta):
        tablename = "animals"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    # favoriteHumans


class Link(ormar.Model):
    class Meta(BaseMeta):
        tablename = "link_table"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    animal_order: int = ormar.Integer(nullable=True)
    human_order: int = ormar.Integer(nullable=True)


class Human(ormar.Model):
    class Meta(BaseMeta):
        tablename = "humans"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    favoriteAnimals: List[Animal] = ormar.ManyToMany(
        Animal,
        through=Link,
        related_name="favoriteHumans",
        orders_by=["link__animal_order"],
        related_orders_by=["link__human_order"],
    )


class Human2(ormar.Model):
    class Meta(BaseMeta):
        tablename = "humans2"

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    favoriteAnimals: List[Animal] = ormar.ManyToMany(
        Animal, related_name="favoriteHumans2", orders_by=["link__animal_order__fail"]
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_ordering_by_through_fail():
    async with database:
        alice = await Human2(name="Alice").save()
        spot = await Animal(name="Spot").save()
        await alice.favoriteAnimals.add(spot)
        with pytest.raises(ModelDefinitionError):
            await alice.load_all()


def get_filtered_query(
        sender: Type[Model], instance: Model, to_class: Type[Model]
) -> QuerySet:
    pk = getattr(instance, f"{to_class.get_name()}").pk
    filter_kwargs = {f"{to_class.get_name()}": pk}
    query = sender.objects.filter(**filter_kwargs)
    return query


async def populate_order_on_insert(
        sender: Type[Model], instance: Model, from_class: Type[Model],
        to_class: Type[Model]
):
    order_column = f"{from_class.get_name()}_order"
    if getattr(instance, order_column) is None:
        query = get_filtered_query(sender, instance, to_class)
        max_order = await query.max(order_column)
        max_order = max_order + 1 if max_order is not None else 0
        setattr(instance, order_column, max_order)
    else:
        await reorder_on_update(sender, instance, from_class, to_class,
                                passed_args={
                                    order_column: getattr(instance, order_column)})


async def reorder_on_update(
        sender: Type[Model], instance: Model, from_class: Type[Model],
        to_class: Type[Model], passed_args: Dict
):
    order = f"{from_class.get_name()}_order"
    if order in passed_args:
        query = get_filtered_query(sender, instance, to_class)
        to_reorder = await query.exclude(pk=instance.pk).order_by(order).all()
        old_order = getattr(instance, order)
        new_order = passed_args.get(order)
        if to_reorder:
            for link in to_reorder:
                setattr(link, order, getattr(link, order) + 1)
            await sender.objects.bulk_update(to_reorder, columns=[order])
        check = await get_filtered_query(sender, instance, to_class).all()
        print('reordered', check)


@pre_save(Link)
async def order_link_on_insert(sender: Type[Model], instance: Model, **kwargs: Any):
    relations = list(instance.extract_related_names())
    rel_one = sender.Meta.model_fields[relations[0]].to
    rel_two = sender.Meta.model_fields[relations[1]].to
    await populate_order_on_insert(sender, instance, from_class=rel_one,
                                   to_class=rel_two)
    await populate_order_on_insert(sender, instance, from_class=rel_two,
                                   to_class=rel_one)


@pre_update(Link)
async def reorder_links_on_update(
        sender: Type[ormar.Model], instance: ormar.Model, passed_args: Dict,
        **kwargs: Any
):
    relations = list(instance.extract_related_names())
    rel_one = sender.Meta.model_fields[relations[0]].to
    rel_two = sender.Meta.model_fields[relations[1]].to
    await reorder_on_update(sender, instance, from_class=rel_one, to_class=rel_two,
                            passed_args=passed_args)
    await reorder_on_update(sender, instance, from_class=rel_two, to_class=rel_one,
                            passed_args=passed_args)


@pytest.mark.asyncio
async def test_ordering_by_through_on_m2m_field():
    async with database:
        def verify_order(instance, expected):
            field_name = (
                "favoriteAnimals" if isinstance(instance,
                                                Human) else "favoriteHumans"
            )
            assert [x.name for x in getattr(instance, field_name)] == expected

        alice = await Human(name="Alice").save()
        bob = await Human(name="Bob").save()
        charlie = await Human(name="Charlie").save()

        spot = await Animal(name="Spot").save()
        kitty = await Animal(name="Kitty").save()
        noodle = await Animal(name="Noodle").save()

        await alice.favoriteAnimals.add(noodle)
        await alice.favoriteAnimals.add(spot)
        await alice.favoriteAnimals.add(kitty)

        await alice.load_all()
        verify_order(alice, ["Noodle", "Spot", "Kitty"])

        await bob.favoriteAnimals.add(noodle)
        await bob.favoriteAnimals.add(kitty)
        await bob.favoriteAnimals.add(spot)

        await bob.load_all()
        verify_order(bob, ["Noodle", "Kitty", "Spot"])

        await charlie.favoriteAnimals.add(kitty)
        await charlie.favoriteAnimals.add(noodle)
        await charlie.favoriteAnimals.add(spot)

        await charlie.load_all()
        verify_order(charlie, ["Kitty", "Noodle", "Spot"])

        animals = [noodle, kitty, spot]
        for animal in animals:
            await animal.load_all()
            verify_order(animal, ["Alice", "Bob", "Charlie"])

        zack = await Human(name="Zack").save()

        await noodle.favoriteHumans.add(zack, animal_order=0, human_order=0)
        await noodle.load_all()
        verify_order(noodle, ["Zack", "Alice", "Bob", "Charlie"])

        await zack.load_all()
        verify_order(zack, ["Noodle"])

        await noodle.favoriteHumans.filter(name='Zack').update(
            link=dict(human_order=1))
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Zack", "Bob", "Charlie"])

        await noodle.favoriteHumans.filter(name='Zack').update(
            link=dict(human_order=2))
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Bob", "Zack", "Charlie"])

        await noodle.favoriteHumans.filter(name='Zack').update(
            link=dict(human_order=3))
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Bob", "Charlie", "Zack"])

        await kitty.favoriteHumans.remove(bob)
        await kitty.load_all()
        assert [x.name for x in kitty.favoriteHumans] == ["Alice", "Charlie"]

        bob = await noodle.favoriteHumans.get(pk=bob.pk)
        assert bob.link.human_order == 1

        await noodle.favoriteHumans.remove(
            await noodle.favoriteHumans.filter(link__human_order=2).get()
        )
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Bob", "Zack"])
