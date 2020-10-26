from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI

import ormar

app = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database("sqlite:///test.db")
app.state.database = database


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)


class Item(ormar.Model):
    class Meta:
        tablename = "items"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    category: ormar.ForeignKey(Category, nullable=True)


@app.get("/items/", response_model=List[Item])
async def get_items():
    items = await Item.objects.select_related("category").all()
    return items


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    await item.save()
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


@app.put("/items/{item_id}")
async def get_item(item_id: int, item: Item):
    item_db = await Item.objects.get(pk=item_id)
    return await item_db.update(**item.dict())


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, item: Item):
    item_db = await Item.objects.get(pk=item_id)
    return {"deleted_rows": await item_db.delete()}
