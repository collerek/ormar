import databases
import pytest
import sqlalchemy

import ormar
from ormar import ModelMeta
from ormar.exceptions import QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ModelMeta):
    metadata = metadata
    database = database


class Car(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class UsersCar(ormar.Model):
    class Meta(BaseMeta):
        tablename = "cars_x_users"


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    cars = ormar.ManyToMany(Car, through=UsersCar)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_limit_zero():
    async with database:
        async with database.transaction(force_rollback=True):
            for i in range(5):
                await Car(name=f"{i}").save()

            cars = await Car.objects.limit(0).all()
            assert cars == []
            assert len(cars) == 0


@pytest.mark.asyncio
async def test_pagination_errors():
    async with database:
        async with database.transaction(force_rollback=True):
            with pytest.raises(QueryDefinitionError):
                await Car.objects.paginate(0).all()

            with pytest.raises(QueryDefinitionError):
                await Car.objects.paginate(1, page_size=0).all()


@pytest.mark.asyncio
async def test_pagination_on_single_model():
    async with database:
        async with database.transaction(force_rollback=True):
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
    async with database:
        async with database.transaction(force_rollback=True):
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
async def test_slice_getitem_queryset_exceptions():
    async with database:
        async with database.transaction(force_rollback=True):
            with pytest.raises(TypeError):
                await Car.objects["foo"].all()

            with pytest.raises(ValueError):
                await Car.objects[-1].all()

            with pytest.raises(ValueError):
                await Car.objects[::2].all()

            with pytest.raises(ValueError):
                await Car.objects[-2:-1].all()


@pytest.mark.asyncio
async def test_slice_getitem_queryset_on_single_model():
    async with database:
        async with database.transaction(force_rollback=True):
            for i in range(10):
                await Car(name=f"{i}").save()

            cars_page1 = await Car.objects[2:8].all()
            assert len(cars_page1) == 6
            assert cars_page1[0].name == "2"
            assert cars_page1[-1].name == "7"

            cars_page2 = await Car.objects[2:].all()
            assert len(cars_page2) == 8
            assert cars_page2[0].name == "2"
            assert cars_page2[-1].name == "9"

            cars_page3 = await Car.objects[:8].all()
            assert len(cars_page3) == 8
            assert cars_page3[0].name == "0"
            assert cars_page3[-1].name == "7"

            cars_page4 = await Car.objects[5].all()
            assert len(cars_page4) == 1
            assert cars_page4[0].name == "5"

            cars_page5 = await Car.objects[8:2].all()
            assert len(cars_page5) == 0
            assert cars_page5 == []


@pytest.mark.asyncio
async def test_slice_getitem_queryset_on_proxy():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User(name="Sep").save()

            for i in range(20):
                c = await Car(name=f"{i}").save()
                await user.cars.add(c)

            cars_page1 = user.cars[:5]
            assert len(cars_page1) == 5
            assert cars_page1[0].name == "0"
            assert cars_page1[4].name == "4"

            cars_page2 = user.cars[5:10]
            assert len(cars_page2) == 5
            assert cars_page2[0].name == "5"
            assert cars_page2[4].name == "9"

            cars_page3 = user.cars[10:]
            assert len(cars_page3) == 10
            assert cars_page3[0].name == "10"
