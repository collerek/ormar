import uuid
from typing import ClassVar

import pytest
from pydantic import model_validator

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Mol(ormar.Model):
    # fixed namespace to generate always unique uuid from the smiles
    _UUID_NAMESPACE: ClassVar[uuid.UUID] = uuid.UUID(
        "12345678-abcd-1234-abcd-123456789abc"
    )

    ormar_config = base_ormar_config.copy(tablename="mols")

    id: uuid.UUID = ormar.UUID(primary_key=True, index=True, uuid_format="hex")
    smiles: str = ormar.String(nullable=False, unique=True, max_length=256)

    def __init__(self, **kwargs):
        # this is required to generate id from smiles in init, if id is not given
        if "id" not in kwargs:
            kwargs["id"] = self._UUID_NAMESPACE
        super().__init__(**kwargs)

    @model_validator(mode="before")
    def make_canonical_smiles_and_uuid(cls, values):
        values["id"], values["smiles"] = cls.uuid(values["smiles"])
        return values

    @classmethod
    def uuid(cls, smiles):
        id_ = uuid.uuid5(cls._UUID_NAMESPACE, smiles)
        return id_, smiles


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_json_column():
    async with base_ormar_config.database:
        await Mol.objects.create(smiles="Cc1ccccc1")
        count = await Mol.objects.count()
        assert count == 1
