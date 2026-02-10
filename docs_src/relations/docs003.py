from typing import Dict, Optional, Union

import ormar
import sqlalchemy
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///relations_docs003.db"

ormar_base_config = ormar.OrmarConfig(
    database=DatabaseConnection(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Department(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    department: Optional[Union[Department, Dict]] = ormar.ForeignKey(Department)
