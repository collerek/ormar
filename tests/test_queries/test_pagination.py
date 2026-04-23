import pytest

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Car(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class UsersCar(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cars_x_users")


class User(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    cars = ormar.ManyToMany(Car, through=UsersCar)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_limit_zero():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(5):
                await Car(name=f"{i}").save()

            cars = await Car.objects.limit(0).all()
            assert cars == []
            assert len(cars) == 0


@pytest.mark.asyncio
async def test_pagination_errors():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            with pytest.raises(QueryDefinitionError):
                await Car.objects.paginate(0).all()

            with pytest.raises(QueryDefinitionError):
                await Car.objects.paginate(1, page_size=0).all()


@pytest.mark.asyncio
async def test_pagination_on_single_model():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(20):
                await Car(name=f"{i}").save()

            cars_page1 = await Car.objects.paginate(1, page_size=5).all()
            assert len(cars_page1) == 5
            assert cars_page1[0].name == "0"
            assert cars_page1[4].name == "4"
            cars_page2 = await Car.objects.paginate(2, page_size=5).all()
            assert len(cars_page2) == 5
            assert cars_page2[0].name == "5"
            assert cars_page2[4].name == "9"

            all_cars = await Car.objects.paginate(1).all()
            assert len(all_cars) == 20

            half_cars = await Car.objects.paginate(2, page_size=10).all()
            assert len(half_cars) == 10
            assert half_cars[0].name == "10"


@pytest.mark.asyncio
async def test_proxy_pagination():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            user = await User(name="Jon").save()

            for i in range(20):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            await user.cars.paginate(1, page_size=5).all()
            assert len(user.cars) == 5
            assert user.cars[0].name == "0"
            assert user.cars[4].name == "4"

            await user.cars.paginate(2, page_size=5).all()
            assert len(user.cars) == 5
            assert user.cars[0].name == "5"
            assert user.cars[4].name == "9"

            await user.cars.paginate(1).all()
            assert len(user.cars) == 20

            await user.cars.paginate(2, page_size=10).all()
            assert len(user.cars) == 10
            assert user.cars[0].name == "10"


@pytest.mark.asyncio
async def test_slice_rejects_invalid_types_and_shapes():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            with pytest.raises(QueryDefinitionError):
                Car.objects["foo"]  # type: ignore[index]

            with pytest.raises(QueryDefinitionError):
                Car.objects[::2]

            with pytest.raises(QueryDefinitionError):
                Car.objects[:-2]

            with pytest.raises(QueryDefinitionError):
                Car.objects[2:-5]

            with pytest.raises(QueryDefinitionError):
                Car.objects[-5:2]


@pytest.mark.asyncio
async def test_slice_positive_bounds():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            cars_mid = await Car.objects[2:8].all()
            assert len(cars_mid) == 6
            assert cars_mid[0].name == "2"
            assert cars_mid[-1].name == "7"

            cars_tail = await Car.objects[2:].all()
            assert len(cars_tail) == 8
            assert cars_tail[0].name == "2"
            assert cars_tail[-1].name == "9"

            cars_head = await Car.objects[:8].all()
            assert len(cars_head) == 8
            assert cars_head[0].name == "0"
            assert cars_head[-1].name == "7"

            single = await Car.objects[5].all()
            assert len(single) == 1
            assert single[0].name == "5"

            empty = await Car.objects[8:2].all()
            assert empty == []

            all_cars = await Car.objects[:].all()
            assert len(all_cars) == 10


@pytest.mark.asyncio
async def test_slice_negative_returns_tail_in_original_order():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            last_three = await Car.objects[-3:].all()
            assert [c.name for c in last_three] == ["7", "8", "9"]

            last_one = await Car.objects[-1].all()
            assert [c.name for c in last_one] == ["9"]

            middle_from_tail = await Car.objects[-5:-2].all()
            assert [c.name for c in middle_from_tail] == ["5", "6", "7"]

            empty_reversed = await Car.objects[-2:-5].all()
            assert empty_reversed == []


@pytest.mark.asyncio
async def test_slice_respects_user_order_by():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            desc_head = await Car.objects.order_by("-name")[:3].all()
            assert [c.name for c in desc_head] == ["9", "8", "7"]

            desc_tail = await Car.objects.order_by("-name")[-3:].all()
            assert [c.name for c in desc_tail] == ["2", "1", "0"]


@pytest.mark.asyncio
async def test_slice_with_filter_chaining():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            filtered_tail = await Car.objects.filter(id__gte=3)[-2:].all()
            assert [c.name for c in filtered_tail] == ["8", "9"]


@pytest.mark.asyncio
async def test_proxy_slice_positive_and_negative():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            user = await User(name="Sep").save()

            for i in range(10):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            await user.cars.filter(id__gte=0)[:5].all()
            assert len(user.cars) == 5
            assert user.cars[0].name == "0"
            assert user.cars[4].name == "4"

            await user.cars.filter(id__gte=0)[-3:].all()
            assert [c.name for c in user.cars] == ["7", "8", "9"]

            await user.cars.filter(id__gte=0)[-1].all()
            assert len(user.cars) == 1
            assert user.cars[0].name == "9"


@pytest.mark.asyncio
async def test_slice_chained_after_negative_recanonicalizes():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            sliced_again = await Car.objects[-3:][:2].all()
            assert [c.name for c in sliced_again] == ["0", "1"]


@pytest.mark.asyncio
async def test_proxy_first_or_none():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            user = await User(name="Jon").save()

            assert await user.cars.first_or_none() is None

            for i in range(3):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            first_car = await user.cars.first_or_none()
            assert first_car is not None
            assert first_car.name == "0"

            assert await user.cars.first_or_none(name="missing") is None


@pytest.mark.asyncio
async def test_proxy_last_and_last_or_none():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            user = await User(name="Jon").save()

            assert await user.cars.last_or_none() is None

            for i in range(5):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            last_car = await user.cars.last()
            assert last_car.name == "4"

            filtered = await user.cars.last(name="2")
            assert filtered.name == "2"

            existing = await user.cars.last_or_none(name="3")
            assert existing is not None
            assert existing.name == "3"

            assert await user.cars.last_or_none(name="missing") is None


@pytest.mark.asyncio
async def test_last_with_prefetch_related():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            user = await User(name="Tom").save()
            for i in range(3):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            last_user = await User.objects.prefetch_related("cars").last()
            assert last_user.name == "Tom"
            assert len(last_user.cars) == 3
