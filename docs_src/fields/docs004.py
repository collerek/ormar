from datetime import datetime

import sqlalchemy
from sqlalchemy import func, text

import ormar
from ormar import DatabaseConnection

database = DatabaseConnection("sqlite+aiosqlite:///fields_docs004.db")
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        database=database, metadata=metadata, tablename="product"
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200, server_default="Acme")
    sort_order: int = ormar.Integer(server_default=text("10"))
    created: datetime = ormar.DateTime(server_default=func.now())
