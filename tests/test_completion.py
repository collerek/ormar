import ormar

from tests.settings import create_config

base_ormar_config = create_config()


class Department(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
