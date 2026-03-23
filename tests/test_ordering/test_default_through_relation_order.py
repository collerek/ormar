from typing import Any, Optional, cast
from uuid import UUID, uuid4

import pytest

import ormar
from ormar import (
    Model,
    ModelDefinitionError,
    QuerySet,
    pre_relation_remove,
    pre_save,
    pre_update,
)
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Animal(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="animals")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    # favoriteHumans


class Link(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="link_table")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    animal_order: Optional[int] = ormar.Integer(nullable=True)
    human_order: Optional[int] = ormar.Integer(nullable=True)


class Human(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="humans")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    favoriteAnimals: list[Animal] = ormar.ManyToMany(
        Animal,
        through=Link,
        related_name="favoriteHumans",
        orders_by=["link__animal_order"],
        related_orders_by=["link__human_order"],
    )


class Human2(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="humans2")

    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.Text(default="")
    favoriteAnimals: list[Animal] = ormar.ManyToMany(
        Animal, related_name="favoriteHumans2", orders_by=["link__animal_order__fail"]
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_ordering_by_through_fail():
    async with base_ormar_config.database:
        alice = await Human2(name="Alice").save()
        spot = await Animal(name="Spot").save()
        await alice.favoriteAnimals.add(spot)
        with pytest.raises(ModelDefinitionError):
            await alice.load_all()


def _get_filtered_query(
    sender: type[Model], instance: Model, to_class: type[Model]
) -> QuerySet:
    """
    Helper function.
    Gets the query filtered by the appropriate class name.
    """
    pk = getattr(instance, f"{to_class.get_name()}").pk
    filter_kwargs = {f"{to_class.get_name()}": pk}
    query = sender.objects.filter(**filter_kwargs)
    return query


def _get_through_model_relations(
    sender: type[Model], instance: Model
) -> tuple[type[Model], type[Model]]:
    relations = list(instance.extract_related_names())
    rel_one = sender.ormar_config.model_fields[relations[0]].to
    rel_two = sender.ormar_config.model_fields[relations[1]].to
    return rel_one, rel_two


async def _populate_order_on_insert(
    sender: type[Model], instance: Model, from_class: type[Model], to_class: type[Model]
):
    """
    Helper function.

    Get max values from database for both orders and adds 1 (0 if max is None) if the
    order is not provided. If the order is provided it reorders the existing links
    to match the newly defined order.

    Assumes names f"{model.get_name()}_order" like for Animal: animal_order.
    """
    order_column = f"{from_class.get_name()}_order"
    if getattr(instance, order_column) is None:
        query = _get_filtered_query(sender, instance, to_class)
        max_order = await query.max(order_column)
        max_order = max_order + 1 if max_order is not None else 0
        setattr(instance, order_column, max_order)
    else:
        await _reorder_on_update(
            sender=sender,
            instance=instance,
            from_class=from_class,
            to_class=to_class,
            passed_args={order_column: getattr(instance, order_column)},
        )


async def _reorder_on_update(
    sender: type[Model],
    instance: Model,
    from_class: type[Model],
    to_class: type[Model],
    passed_args: dict,
):
    """
    Helper function.
    Actually reorders links by given order passed in add/update query to the link
    model.

    Assumes names f"{model.get_name()}_order" like for Animal: animal_order.
    """
    order = f"{from_class.get_name()}_order"
    if order in passed_args:
        query = _get_filtered_query(sender, instance, to_class)
        to_reorder = await query.exclude(pk=instance.pk).order_by(order).all()
        new_order = passed_args.get(order)
        if to_reorder and new_order is not None:
            # can be more efficient - here we renumber all even if not needed.
            for ind, link in enumerate(to_reorder):
                if ind < new_order:
                    setattr(link, order, ind)
                else:
                    setattr(link, order, ind + 1)
            await sender.objects.bulk_update(
                cast(list[Model], to_reorder), columns=[order]
            )


@pre_save(Link)
async def order_link_on_insert(sender: type[Model], instance: Model, **kwargs: Any):
    """
    Signal receiver registered on Link model, triggered every time before one is created
    by calling save() on a model. Note that signal functions for pre_save signal accepts
    sender class, instance and have to accept **kwargs even if it's empty as of now.
    """
    rel_one, rel_two = _get_through_model_relations(sender, instance)
    await _populate_order_on_insert(
        sender=sender, instance=instance, from_class=rel_one, to_class=rel_two
    )
    await _populate_order_on_insert(
        sender=sender, instance=instance, from_class=rel_two, to_class=rel_one
    )


@pre_update(Link)
async def reorder_links_on_update(
    sender: type[ormar.Model], instance: ormar.Model, passed_args: dict, **kwargs: Any
):
    """
    Signal receiver registered on Link model, triggered every time before one is updated
    by calling update() on a model. Note that signal functions for pre_update signal
    accepts sender class, instance, passed_args which is a dict of kwargs passed to
    update and have to accept **kwargs even if it's empty as of now.
    """

    rel_one, rel_two = _get_through_model_relations(sender, instance)
    await _reorder_on_update(
        sender=sender,
        instance=instance,
        from_class=rel_one,
        to_class=rel_two,
        passed_args=passed_args,
    )
    await _reorder_on_update(
        sender=sender,
        instance=instance,
        from_class=rel_two,
        to_class=rel_one,
        passed_args=passed_args,
    )


@pre_relation_remove([Animal, Human])
async def reorder_links_on_remove(
    sender: type[ormar.Model],
    instance: ormar.Model,
    child: ormar.Model,
    relation_name: str,
    **kwargs: Any,
):
    """
    Signal receiver registered on Anima and Human models, triggered every time before
    relation on a model is removed. Note that signal functions for pre_relation_remove
    signal accepts sender class, instance, child, relation_name and have to accept
    **kwargs even if it's empty as of now.

    Note that if classes have many relations you need to check if current one is ordered
    """
    through_class = sender.ormar_config.model_fields[relation_name].through
    through_instance = getattr(instance, through_class.get_name())
    if not through_instance:
        parent_pk = instance.pk
        child_pk = child.pk
        filter_kwargs = {f"{sender.get_name()}": parent_pk, child.get_name(): child_pk}
        through_instance = await through_class.objects.get(**filter_kwargs)
    rel_one, rel_two = _get_through_model_relations(through_class, through_instance)
    await _reorder_on_update(
        sender=through_class,
        instance=through_instance,
        from_class=rel_one,
        to_class=rel_two,
        passed_args={f"{rel_one.get_name()}_order": 999999},
    )
    await _reorder_on_update(
        sender=through_class,
        instance=through_instance,
        from_class=rel_two,
        to_class=rel_one,
        passed_args={f"{rel_two.get_name()}_order": 999999},
    )


@pytest.mark.asyncio
async def test_ordering_by_through_on_m2m_field():
    async with base_ormar_config.database:

        def verify_order(instance, expected):
            field_name = (
                "favoriteAnimals" if isinstance(instance, Human) else "favoriteHumans"
            )
            order_field_name = (
                "animal_order" if isinstance(instance, Human) else "human_order"
            )
            assert [x.name for x in getattr(instance, field_name)] == expected
            assert [
                getattr(x.link, order_field_name) for x in getattr(instance, field_name)
            ] == [i for i in range(len(expected))]

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

        await noodle.favoriteHumans.add(zack, human_order=0)
        await noodle.load_all()
        verify_order(noodle, ["Zack", "Alice", "Bob", "Charlie"])

        await zack.load_all()
        verify_order(zack, ["Noodle"])

        await noodle.favoriteHumans.filter(name="Zack").update(link=dict(human_order=1))
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Zack", "Bob", "Charlie"])

        await noodle.favoriteHumans.filter(name="Zack").update(link=dict(human_order=2))
        await noodle.load_all()
        verify_order(noodle, ["Alice", "Bob", "Zack", "Charlie"])

        await noodle.favoriteHumans.filter(name="Zack").update(link=dict(human_order=3))
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
