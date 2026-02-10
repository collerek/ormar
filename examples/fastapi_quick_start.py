from contextlib import asynccontextmanager
from typing import List, Optional

import ormar
import sqlalchemy
import uvicorn
from fastapi import FastAPI

DATABASE_URL = "sqlite+aiosqlite:///test.db"

ormar_base_config = ormar.OrmarConfig(
    database=ormar.DatabaseConnection(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()
    yield
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


app = FastAPI(lifespan=lifespan)
metadata = sqlalchemy.MetaData()
database = ormar.DatabaseConnection(DATABASE_URL)
app.state.database = database


class Category(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


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
    return await item_db.update(**item.model_dump())


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, item: Item = None):
    if item:
        return {"deleted_rows": await item.delete()}
    item_db = await Item.objects.get(pk=item_id)
    return {"deleted_rows": await item_db.delete()}


if __name__ == "__main__":
    # to play with API run the script and visit http://127.0.0.1:8000/docs
    uvicorn.run(app, host="127.0.0.1", port=8000)
