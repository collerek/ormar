import uuid

import pytest

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users3")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="")


class User2(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users4")

    id: uuid.UUID = ormar.UUID(
        uuid_format="string", primary_key=True, default=uuid.uuid4
    )
    name: str = ormar.String(max_length=100, default="")


class Task(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tasks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="")
    user: User = ormar.ForeignKey(to=User)


class Task2(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tasks2")

    id: uuid.UUID = ormar.UUID(
        uuid_format="string", primary_key=True, default=uuid.uuid4
    )
    name: str = ormar.String(max_length=100, default="")
    user: User2 = ormar.ForeignKey(to=User2)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_empty_result():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            async for user in User.objects.iterate():
                pass  # pragma: no cover


@pytest.mark.asyncio
async def test_model_iterator():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            jane = await User.objects.create(name="Jane")
            lucy = await User.objects.create(name="Lucy")

            async for user in User.objects.iterate():
                assert user in (tom, jane, lucy)


@pytest.mark.asyncio
async def test_model_iterator_filter():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            await User.objects.create(name="Jane")
            await User.objects.create(name="Lucy")

            async for user in User.objects.iterate(name="Tom"):
                assert user.name == tom.name


@pytest.mark.asyncio
async def test_model_iterator_relations():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            jane = await User.objects.create(name="Jane")
            lucy = await User.objects.create(name="Lucy")

            for user in tom, jane, lucy:
                await Task.objects.create(name="task1", user=user)
                await Task.objects.create(name="task2", user=user)

            results = []
            async for user in User.objects.select_related(User.tasks).iterate():
                assert len(user.tasks) == 2
                results.append(user)

            assert len(results) == 3


@pytest.mark.asyncio
async def test_model_iterator_relations_queryset_proxy():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            jane = await User.objects.create(name="Jane")

            for user in tom, jane:
                await Task.objects.create(name="task1", user=user)
                await Task.objects.create(name="task2", user=user)

            tom_tasks = []
            async for task in tom.tasks.iterate():
                assert task.name in ("task1", "task2")
                tom_tasks.append(task)

            assert len(tom_tasks) == 2

            jane_tasks = []
            async for task in jane.tasks.iterate():
                assert task.name in ("task1", "task2")
                jane_tasks.append(task)

            assert len(jane_tasks) == 2


@pytest.mark.asyncio
async def test_model_iterator_uneven_number_of_relations():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User.objects.create(name="Tom")
            jane = await User.objects.create(name="Jane")
            lucy = await User.objects.create(name="Lucy")

            for user in tom, jane:
                await Task.objects.create(name="task1", user=user)
                await Task.objects.create(name="task2", user=user)

            await Task.objects.create(name="task3", user=lucy)
            expected_counts = {"Tom": 2, "Jane": 2, "Lucy": 1}
            results = []
            async for user in User.objects.select_related(User.tasks).iterate():
                assert len(user.tasks) == expected_counts[user.name]
                results.append(user)

            assert len(results) == 3


@pytest.mark.asyncio
async def test_model_iterator_uuid_pk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User2.objects.create(name="Tom")
            jane = await User2.objects.create(name="Jane")
            lucy = await User2.objects.create(name="Lucy")

            async for user in User2.objects.iterate():
                assert user in (tom, jane, lucy)


@pytest.mark.asyncio
async def test_model_iterator_filter_uuid_pk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User2.objects.create(name="Tom")
            await User2.objects.create(name="Jane")
            await User2.objects.create(name="Lucy")

            async for user in User2.objects.iterate(name="Tom"):
                assert user.name == tom.name


@pytest.mark.asyncio
async def test_model_iterator_relations_uuid_pk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User2.objects.create(name="Tom")
            jane = await User2.objects.create(name="Jane")
            lucy = await User2.objects.create(name="Lucy")

            for user in tom, jane, lucy:
                await Task2.objects.create(name="task1", user=user)
                await Task2.objects.create(name="task2", user=user)

            results = []
            async for user in User2.objects.select_related(User2.task2s).iterate():
                assert len(user.task2s) == 2
                results.append(user)

            assert len(results) == 3


@pytest.mark.asyncio
async def test_model_iterator_relations_queryset_proxy_uuid_pk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User2.objects.create(name="Tom")
            jane = await User2.objects.create(name="Jane")

            for user in tom, jane:
                await Task2.objects.create(name="task1", user=user)
                await Task2.objects.create(name="task2", user=user)

            tom_tasks = []
            async for task in tom.task2s.iterate():
                assert task.name in ("task1", "task2")
                tom_tasks.append(task)

            assert len(tom_tasks) == 2

            jane_tasks = []
            async for task in jane.task2s.iterate():
                assert task.name in ("task1", "task2")
                jane_tasks.append(task)

            assert len(jane_tasks) == 2


@pytest.mark.asyncio
async def test_model_iterator_uneven_number_of_relations_uuid_pk():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tom = await User2.objects.create(name="Tom")
            jane = await User2.objects.create(name="Jane")
            lucy = await User2.objects.create(name="Lucy")

            for user in tom, jane:
                await Task2.objects.create(name="task1", user=user)
                await Task2.objects.create(name="task2", user=user)

            await Task2.objects.create(name="task3", user=lucy)

            expected_counts = {"Tom": 2, "Jane": 2, "Lucy": 1}

            results = []
            async for user in User2.objects.select_related(User2.task2s).iterate():
                assert len(user.task2s) == expected_counts[user.name]
                results.append(user)

            assert len(results) == 3


@pytest.mark.asyncio
async def test_model_iterator_with_prefetch_raises_error():
    async with base_ormar_config.database:
        with pytest.raises(QueryDefinitionError):
            async for user in User.objects.prefetch_related(User.tasks).iterate():
                pass  # pragma: no cover
