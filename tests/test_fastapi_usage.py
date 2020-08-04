import json
from typing import Optional

import databases
import pydantic
import sqlalchemy
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

import orm
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Item(orm.Model):
    __tablename__ = "users"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


client = TestClient(app)


def test_read_main():
    response = client.post("/items/", json={'name': 'test', 'id': 1})
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {'name': 'test', 'id': 1}
    item = Item(**response.json())
    assert item.id == 1
