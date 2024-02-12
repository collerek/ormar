import ormar
import pytest
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
