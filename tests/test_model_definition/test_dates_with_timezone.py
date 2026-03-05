from datetime import date, datetime, time, timedelta, timezone

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class DateFieldsModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    created_date: datetime = ormar.DateTime(
        default=datetime.now(tz=timezone(timedelta(hours=3))), timezone=True
    )
    updated_date: datetime = ormar.DateTime(
        default=datetime.now(tz=timezone(timedelta(hours=3))),
        name="modification_date",
        timezone=True,
    )


class SampleModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    updated_at: datetime = ormar.DateTime()


class TimeModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    elapsed: time = ormar.Time()


class DateModel(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    creation_date: date = ormar.Date()


class MyModel(ormar.Model):
    id: int = ormar.Integer(primary_key=True)
    created_at: datetime = ormar.DateTime(timezone=True, nullable=False)

    ormar_config = base_ormar_config.copy(tablename="mymodels")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_model_crud_with_timezone():
    async with base_ormar_config.database:
        datemodel = await DateFieldsModel().save()
        assert datemodel.created_date is not None
        assert datemodel.updated_date is not None


@pytest.mark.asyncio
async def test_query_with_datetime_in_filter():
    async with base_ormar_config.database:
        creation_dt = datetime(2021, 5, 18, 0, 0, 0, 0)
        sample = await SampleModel.objects.create(updated_at=creation_dt)

        current_dt = datetime(2021, 5, 19, 0, 0, 0, 0)
        outdated_samples = await SampleModel.objects.filter(
            updated_at__lt=current_dt
        ).all()

        assert outdated_samples[0] == sample


@pytest.mark.asyncio
async def test_query_with_date_in_filter():
    async with base_ormar_config.database:
        sample = await TimeModel.objects.create(elapsed=time(0, 20, 20))
        await TimeModel.objects.create(elapsed=time(0, 12, 0))
        await TimeModel.objects.create(elapsed=time(0, 19, 55))
        sample4 = await TimeModel.objects.create(elapsed=time(0, 21, 15))

        threshold = time(0, 20, 0)
        samples = await TimeModel.objects.filter(TimeModel.elapsed >= threshold).all()

        assert len(samples) == 2
        assert samples[0] == sample
        assert samples[1] == sample4


@pytest.mark.asyncio
async def test_query_with_time_in_filter():
    async with base_ormar_config.database:
        await DateModel.objects.create(creation_date=date(2021, 5, 18))
        sample2 = await DateModel.objects.create(creation_date=date(2021, 5, 19))
        sample3 = await DateModel.objects.create(creation_date=date(2021, 5, 20))

        outdated_samples = await DateModel.objects.filter(
            creation_date__in=[date(2021, 5, 19), date(2021, 5, 20)]
        ).all()

        assert len(outdated_samples) == 2
        assert outdated_samples[0] == sample2
        assert outdated_samples[1] == sample3


@pytest.mark.asyncio
async def test_filtering_by_timezone_with_timedelta():
    async with base_ormar_config.database:
        now_utc = datetime.now(timezone.utc)
        object = MyModel(created_at=now_utc)
        await object.save()

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        created_since_one_hour_ago = await MyModel.objects.filter(
            created_at__gte=one_hour_ago
        ).all()

        assert len(created_since_one_hour_ago) == 1
