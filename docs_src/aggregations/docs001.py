from typing import Optional

import ormar
import sqlalchemy
from ormar import DatabaseConnection
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///aggregations_docs001.db"

database = DatabaseConnection(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = create_async_engine(DATABASE_URL)


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
    engine=engine,
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
