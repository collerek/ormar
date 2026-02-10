from tests.settings import create_config

base_ormar_config = create_config()

import ormar

ormar_config = base_ormar_config.copy()


class Person(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="person")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)


class Pet(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="pet")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)
    owner: Person = ormar.ForeignKey(Person, ondelete="CASCADE")


def test_fields_exist():
    PetPydantic = Pet.get_pydantic()
    PersonPydantic = Person.get_pydantic(include={"id", "name", "pets"})
    assert "owner" in PetPydantic.model_fields
    assert "pets" in PersonPydantic.model_fields
