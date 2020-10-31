from datetime import datetime

import databases
import sqlalchemy
from sqlalchemy import func, text

import ormar

database = databases.Database("sqlite:///test.db")
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    class Meta:
        tablename = "product"
        metadata = metadata
        database = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)
    company = ormar.String(max_length=200, server_default='Acme')
    sort_order = ormar.Integer(server_default=text("10"))
    created= ormar.DateTime(server_default=func.now())
