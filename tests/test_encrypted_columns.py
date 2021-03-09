# type: ignore
import decimal
import uuid
import datetime
from typing import Any

import databases
import pytest
import sqlalchemy

import ormar
from ormar import ModelDefinitionError
from ormar.fields.sqlalchemy_encrypted import EncryptedString
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


default_fernet = dict(
    encrypt_secret="asd123", encrypt_backend=ormar.EncryptBackends.FERNET,
)


class DummyBackend(ormar.fields.EncryptBackend):
    def _initialize_backend(self, secret_key: bytes) -> None:
        pass

    def encrypt(self, value: Any) -> str:
        return value

    def decrypt(self, value: Any) -> str:
        return value


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, **default_fernet)
    uuid_test = ormar.UUID(default=uuid.uuid4, uuid_format="string")
    uuid_test2 = ormar.UUID(nullable=True, uuid_format="string")
    password: str = ormar.String(
        max_length=128,
        encrypt_secret="udxc32",
        encrypt_backend=ormar.EncryptBackends.HASH,
    )
    birth_year: int = ormar.Integer(
        nullable=True,
        encrypt_secret="secure89key%^&psdijfipew",
        encrypt_max_length=200,
        encrypt_backend=ormar.EncryptBackends.FERNET,
    )
    test_text: str = ormar.Text(default="", **default_fernet)
    test_bool: bool = ormar.Boolean(nullable=False, **default_fernet)
    test_float: float = ormar.Float(**default_fernet)
    test_float2: float = ormar.Float(nullable=True, **default_fernet)
    test_datetime = ormar.DateTime(default=datetime.datetime.now, **default_fernet)
    test_date = ormar.Date(default=datetime.date.today, **default_fernet)
    test_time = ormar.Time(default=datetime.time, **default_fernet)
    test_json = ormar.JSON(default={}, **default_fernet)
    test_bigint: int = ormar.BigInteger(default=0, **default_fernet)
    test_decimal = ormar.Decimal(scale=2, precision=10, **default_fernet)
    test_decimal2 = ormar.Decimal(max_digits=10, decimal_places=2, **default_fernet)
    custom_backend: str = ormar.String(
        max_length=200,
        encrypt_secret="asda8",
        encrypt_backend=ormar.EncryptBackends.CUSTOM,
        encrypt_custom_backend=DummyBackend,
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_error_on_encrypted_pk():
    with pytest.raises(ModelDefinitionError):

        class Wrong(ormar.Model):
            class Meta(BaseMeta):
                tablename = "wrongs"

            id: int = ormar.Integer(
                primary_key=True,
                encrypt_secret="asd123",
                encrypt_backend=ormar.EncryptBackends.FERNET,
            )


def test_error_on_encrypted_relation():
    with pytest.raises(ModelDefinitionError):

        class Wrong2(ormar.Model):
            class Meta(BaseMeta):
                tablename = "wrongs2"

            id: int = ormar.Integer(primary_key=True)
            author = ormar.ForeignKey(
                Author,
                encrypt_secret="asd123",
                encrypt_backend=ormar.EncryptBackends.FERNET,
            )


def test_error_on_encrypted_m2m_relation():
    with pytest.raises(ModelDefinitionError):

        class Wrong3(ormar.Model):
            class Meta(BaseMeta):
                tablename = "wrongs3"

            id: int = ormar.Integer(primary_key=True)
            author = ormar.ManyToMany(
                Author,
                encrypt_secret="asd123",
                encrypt_backend=ormar.EncryptBackends.FERNET,
            )


def test_wrong_backend():
    with pytest.raises(ModelDefinitionError):

        class Wrong3(ormar.Model):
            class Meta(BaseMeta):
                tablename = "wrongs3"

            id: int = ormar.Integer(primary_key=True)
            author = ormar.Integer(
                encrypt_secret="asd123",
                encrypt_backend=ormar.EncryptBackends.CUSTOM,
                encrypt_custom_backend="aa",
            )


def test_db_structure():
    assert Author.Meta.table.c.get("name").type.__class__ == EncryptedString
    assert Author.Meta.table.c.get("birth_year").type.max_length == 200


@pytest.mark.asyncio
async def test_save_and_retrieve():
    async with database:
        test_uuid = uuid.uuid4()
        await Author(
            name="Test",
            birth_year=1988,
            password="test123",
            uuid_test=test_uuid,
            test_float=1.2,
            test_bool=True,
            test_decimal=decimal.Decimal(3.5),
            test_decimal2=decimal.Decimal(5.5),
            test_json=dict(aa=12),
            custom_backend="test12",
        ).save()
        author = await Author.objects.get()

        assert author.name == "Test"
        assert author.birth_year == 1988
        password = (
            "03e4a4d513e99cb3fe4ee3db282c053daa3f3572b849c3868939a306944ad5c08"
            "22b50d4886e10f4cd418c3f2df3ceb02e2e7ac6e920ae0c90f2dedfc8fa16e2"
        )
        assert author.password == password
        assert author.uuid_test == test_uuid
        assert author.uuid_test2 is None
        assert author.test_datetime.date() == datetime.date.today()
        assert author.test_date == datetime.date.today()
        assert author.test_text == ""
        assert author.test_float == 1.2
        assert author.test_float2 is None
        assert author.test_bigint == 0
        assert author.test_json == {"aa": 12}
        assert author.test_decimal == 3.5
        assert author.test_decimal2 == 5.5
        assert author.custom_backend == "test12"
