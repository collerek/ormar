import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.testclient import TestClient

import orm
from tests.settings import DATABASE_URL

app = FastAPI()

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Category(orm.Model):
    __tablename__ = "cateries"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Item(orm.Model):
    __tablename__ = "users"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)
    category = orm.ForeignKey(Category, nullable=True)


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


client = TestClient(app)


def test_read_main():
    response = client.post("/items/", json={'name': 'test', 'id': 1, 'category': {'name': 'test cat'}})
    assert response.status_code == 200
    assert response.json() == {'category': {'id': None, 'name': 'test cat'}, 'id': 1, 'name': 'test'}
    item = Item(**response.json())
    assert item.id == 1
