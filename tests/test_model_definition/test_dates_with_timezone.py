from datetime import timezone, timedelta, datetime, date, time

import databases
import pytest
import sqlalchemy

import ormar

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class DateFieldsModel(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

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
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    updated_at: datetime = ormar.DateTime()


class TimeModel(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    elapsed: time = ormar.Time()


class DateModel(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    creation_date: date = ormar.Date()


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_model_crud_with_timezone():
    async with database:
        datemodel = await DateFieldsModel().save()
        assert datemodel.created_date is not None
        assert datemodel.updated_date is not None


@pytest.mark.asyncio
async def test_query_with_datetime_in_filter():
    async with database:
        creation_dt = datetime(2021, 5, 18, 0, 0, 0, 0)
        sample = await SampleModel.objects.create(updated_at=creation_dt)

        current_dt = datetime(2021, 5, 19, 0, 0, 0, 0)
        outdated_samples = await SampleModel.objects.filter(
            updated_at__lt=current_dt
        ).all()

        assert outdated_samples[0] == sample


@pytest.mark.asyncio
async def test_query_with_date_in_filter():
    async with database:
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
    async with database:
        await DateModel.objects.create(creation_date=date(2021, 5, 18))
        sample2 = await DateModel.objects.create(creation_date=date(2021, 5, 19))
        sample3 = await DateModel.objects.create(creation_date=date(2021, 5, 20))

        outdated_samples = await DateModel.objects.filter(
            creation_date__in=[date(2021, 5, 19), date(2021, 5, 20)]
        ).all()

        assert len(outdated_samples) == 2
        assert outdated_samples[0] == sample2
        assert outdated_samples[1] == sample3
