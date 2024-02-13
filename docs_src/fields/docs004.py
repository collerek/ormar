from datetime import datetime

import databases
import ormar
import sqlalchemy
from sqlalchemy import func, text

database = databases.Database("sqlite:///test.db")
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="product",
        database=database,
        metadata=metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    company: str = ormar.String(max_length=200, server_default="Acme")
    sort_order: int = ormar.Integer(server_default=text("10"))
    created: datetime = ormar.DateTime(server_default=func.now())
