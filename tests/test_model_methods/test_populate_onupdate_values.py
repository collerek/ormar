import base64
import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

import pytest
from sqlalchemy import func

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()

PAST = datetime(2000, 1, 1, 0, 0, 0)


def _past() -> datetime:
    return PAST


class Task(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="tasks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(
        max_length=255,
        on_update=lambda: "hello",
    )
    points: int = ormar.Integer(default=0, minimum=0, on_update=1)
    year: int = ormar.Integer(default=1, on_update=2)
    updated_at: Optional[datetime] = ormar.DateTime(
        default=_past, server_default=func.now(), on_update=datetime.now
    )


class Size(enum.Enum):
    SMALL = "small"
    LARGE = "large"


UPDATED_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class AllTypes(ormar.Model):
    """Covers every ormar field type so on_update is exercised against each."""

    ormar_config = base_ormar_config.copy(tablename="all_types")

    id: int = ormar.Integer(primary_key=True)
    flag: bool = ormar.Boolean(default=False, on_update=True)
    count: int = ormar.Integer(default=0, on_update=42)
    big: int = ormar.BigInteger(default=0, on_update=9_000_000_000)
    small: int = ormar.SmallInteger(default=0, on_update=7)
    ratio: float = ormar.Float(default=0.0, on_update=3.14)
    note: str = ormar.String(max_length=100, default="initial", on_update="updated_s")
    body: str = ormar.Text(default="", on_update="updated_t")
    amount: Decimal = ormar.Decimal(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        on_update=Decimal("9.99"),
    )
    when: datetime = ormar.DateTime(default=_past, on_update=datetime(2030, 1, 1))
    day: date = ormar.Date(default=date(2000, 1, 1), on_update=date(2030, 1, 1))
    clock: time = ormar.Time(default=time(0, 0, 0), on_update=time(12, 30, 45))
    meta: dict = ormar.JSON(default={"v": 0}, on_update={"v": 1})
    token: uuid.UUID = ormar.UUID(
        default=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        on_update=UPDATED_UUID,
    )
    blob: bytes = ormar.LargeBinary(
        max_length=100, default=b"initial_blob", on_update=b"updated_blob"
    )
    blob64: str = ormar.LargeBinary(
        max_length=100,
        represent_as_base64_str=True,
        default=b"initial_b64",
        on_update=b"updated_b64",
    )
    size: Size = ormar.Enum(enum_class=Size, default=Size.SMALL, on_update=Size.LARGE)
    secret: str = ormar.String(
        max_length=100,
        default="initial_secret",
        on_update="updated_secret",
        encrypt_secret="key_for_tests",
        encrypt_backend=ormar.EncryptBackends.FERNET,
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_onupdate_use_setattr_to_update():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="123")
            assert t1.name == "123"
            assert t1.points == 0
            assert t1.year == 1
            assert t1.updated_at == PAST

            t2 = await Task.objects.get(name="123")
            t2.name = "explicit"
            t2.year = 2024
            await t2.update()
            assert t2.name == "explicit"
            assert t2.points == 1
            assert t2.year == 2024
            assert t2.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_use_update_func_kwargs():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="123")
            assert t1.name == "123"
            assert t1.points == 0
            assert t1.year == 1
            assert t1.updated_at == PAST

            t2 = await Task.objects.get(name="123")
            await t2.update(name="from_kwargs")
            assert t2.name == "from_kwargs"
            assert t2.points == 1
            assert t2.year == 2
            assert t2.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_use_update_func_columns():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="123")
            assert t1.name == "123"
            assert t1.points == 0
            assert t1.year == 1
            assert t1.updated_at == PAST

            t2 = await Task.objects.get(name="123")
            await t2.update(_columns=["year"], year=2024)
            assert t2.name == "hello"
            assert t2.points == 1
            assert t2.year == 2024
            assert t2.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_queryset_update():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="123")
            assert t1.name == "123"
            assert t1.points == 0
            assert t1.year == 1
            assert t1.updated_at == PAST

            await Task.objects.filter(name="123").update(name="qs_update")
            t2 = await Task.objects.get(name="qs_update")
            assert t2.name == "qs_update"
            assert t2.points == 1
            assert t2.year == 2
            assert t2.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_upsert():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="upsert_initial")
            assert t1.updated_at == PAST
            t1.name = "upsert_modified"
            await t1.upsert()
            assert t1.name == "upsert_modified"
            assert t1.points == 1
            assert t1.year == 2
            assert t1.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_bulk_update():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Task.objects.create(name="123")
            assert t1.name == "123"
            assert t1.points == 0
            assert t1.year == 1
            assert t1.updated_at == PAST

            t2 = await Task.objects.get(name="123")
            t2.name = "bulk_update"
            await Task.objects.bulk_update([t2])
            t3 = await Task.objects.get(name="bulk_update")
            assert t3.name == "bulk_update"
            assert t3.points == 1
            assert t3.year == 2
            assert t3.updated_at > PAST

            t4 = await Task.objects.get(name="bulk_update")
            t4.year = 2024
            await Task.objects.bulk_update([t4], columns=["year"])
            t5 = await Task.objects.get(year=2024)
            assert t5.year == 2024
            assert t5.points == 1
            assert t5.name == "hello"
            assert t5.updated_at > PAST


@pytest.mark.asyncio
async def test_onupdate_all_field_types():
    """Exercises on_update against every ormar field type."""
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            created = await AllTypes.objects.create(id=1)
            assert created.flag is False
            assert created.count == 0
            assert created.big == 0
            assert created.small == 0
            assert created.ratio == 0.0
            assert created.note == "initial"
            assert created.body == ""
            assert created.amount == Decimal("0.00")
            assert created.when == PAST
            assert created.day == date(2000, 1, 1)
            assert created.clock == time(0, 0, 0)
            assert created.meta == {"v": 0}
            assert created.token == uuid.UUID("00000000-0000-0000-0000-000000000000")
            assert created.blob == b"initial_blob"
            assert created.size is Size.SMALL
            assert created.secret == "initial_secret"

            fetched = await AllTypes.objects.get(id=1)
            await fetched.update()

            reloaded = await AllTypes.objects.get(id=1)
            assert reloaded.flag is True
            assert reloaded.count == 42
            assert reloaded.big == 9_000_000_000
            assert reloaded.small == 7
            assert reloaded.ratio == 3.14
            assert reloaded.note == "updated_s"
            assert reloaded.body == "updated_t"
            assert reloaded.amount == Decimal("9.99")
            assert reloaded.when == datetime(2030, 1, 1)
            assert reloaded.day == date(2030, 1, 1)
            assert reloaded.clock == time(12, 30, 45)
            assert reloaded.meta == {"v": 1}
            assert reloaded.token == UPDATED_UUID
            assert reloaded.blob == b"updated_blob"
            assert reloaded.blob64 == base64.b64encode(b"updated_b64").decode()
            assert reloaded.size is Size.LARGE
            assert reloaded.secret == "updated_secret"
