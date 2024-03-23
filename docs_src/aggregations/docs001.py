from typing import Optional

import databases
import ormar
import sqlalchemy
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors", order_by=["-name"])

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):

    ormar_config = base_ormar_config.copy(
        tablename="books", order_by=["year", "-ranking"]
    )

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    ranking: int = ormar.Integer(nullable=True)
