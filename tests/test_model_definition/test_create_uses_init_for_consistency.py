import uuid
from typing import ClassVar

import databases
import pytest
import sqlalchemy
from pydantic import root_validator

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Mol(ormar.Model):
    # fixed namespace to generate always unique uuid from the smiles
    _UUID_NAMESPACE: ClassVar[uuid.UUID] = uuid.UUID(
        "12345678-abcd-1234-abcd-123456789abc"
    )

    class Meta(BaseMeta):
        tablename = "mols"

    id: str = ormar.UUID(primary_key=True, index=True, uuid_format="hex")
    smiles: str = ormar.String(nullable=False, unique=True, max_length=256)

    def __init__(self, **kwargs):
        # this is required to generate id from smiles in init, if id is not given
        if "id" not in kwargs:
            kwargs["id"] = self._UUID_NAMESPACE
        super().__init__(**kwargs)

    @root_validator()
    def make_canonical_smiles_and_uuid(cls, values):
        values["id"], values["smiles"] = cls.uuid(values["smiles"])
        return values

    @classmethod
    def uuid(cls, smiles):
        id_ = uuid.uuid5(cls._UUID_NAMESPACE, smiles)
        return id_, smiles


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_json_column():
    async with database:
        await Mol.objects.create(smiles="Cc1ccccc1")
        count = await Mol.objects.count()
        assert count == 1
