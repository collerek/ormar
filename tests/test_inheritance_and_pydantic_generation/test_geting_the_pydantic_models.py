from typing import List, Optional

import databases
import pydantic
import sqlalchemy
from pydantic import ConstrainedStr

import ormar
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    class Meta:
        tablename = "items"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="test")
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


def test_getting_pydantic_model():
    PydanticCategory = Category.get_pydantic()
    assert issubclass(PydanticCategory, pydantic.BaseModel)
    assert {*PydanticCategory.__fields__.keys()} == {"items", "id", "name"}

    assert not PydanticCategory.__fields__["id"].required
    assert PydanticCategory.__fields__["id"].outer_type_ == int
    assert PydanticCategory.__fields__["id"].default is None

    assert PydanticCategory.__fields__["name"].required
    assert issubclass(PydanticCategory.__fields__["name"].outer_type_, ConstrainedStr)
    assert PydanticCategory.__fields__["name"].default is None

    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert PydanticCategory.__fields__["items"].outer_type_ == List[PydanticItem]
    assert issubclass(PydanticItem, pydantic.BaseModel)
    assert not PydanticItem.__fields__["name"].required
    assert PydanticItem.__fields__["name"].default == "test"
    assert issubclass(PydanticItem.__fields__["name"].outer_type_, ConstrainedStr)
    assert "category" not in PydanticItem.__fields__


def test_getting_pydantic_model_include():
    PydanticCategory = Category.get_pydantic(include={"id", "name"})
    assert len(PydanticCategory.__fields__) == 2
    assert "items" not in PydanticCategory.__fields__


def test_getting_pydantic_model_nested_include_set():
    PydanticCategory = Category.get_pydantic(include={"id", "items__id"})
    assert len(PydanticCategory.__fields__) == 2
    assert "name" not in PydanticCategory.__fields__
    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert len(PydanticItem.__fields__) == 1
    assert "id" in PydanticItem.__fields__


def test_getting_pydantic_model_nested_include_dict():
    PydanticCategory = Category.get_pydantic(include={"id": ..., "items": {"id"}})
    assert len(PydanticCategory.__fields__) == 2
    assert "name" not in PydanticCategory.__fields__
    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert len(PydanticItem.__fields__) == 1
    assert "id" in PydanticItem.__fields__


def test_getting_pydantic_model_nested_include_nested_dict():
    PydanticCategory = Category.get_pydantic(include={"id": ..., "items": {"id": ...}})
    assert len(PydanticCategory.__fields__) == 2
    assert "name" not in PydanticCategory.__fields__
    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert len(PydanticItem.__fields__) == 1
    assert "id" in PydanticItem.__fields__


def test_getting_pydantic_model_include_exclude():
    PydanticCategory = Category.get_pydantic(
        include={"id": ..., "items": {"id", "name"}}, exclude={"items__name"}
    )
    assert len(PydanticCategory.__fields__) == 2
    assert "name" not in PydanticCategory.__fields__
    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert len(PydanticItem.__fields__) == 1
    assert "id" in PydanticItem.__fields__


def test_getting_pydantic_model_exclude():
    PydanticItem = Item.get_pydantic(exclude={"category__name"})
    assert len(PydanticItem.__fields__) == 3
    assert "category" in PydanticItem.__fields__
    PydanticCategory = PydanticItem.__fields__["category"].type_
    assert len(PydanticCategory.__fields__) == 1
    assert "name" not in PydanticCategory.__fields__


def test_getting_pydantic_model_exclude_dict():
    PydanticItem = Item.get_pydantic(exclude={"id": ..., "category": {"name"}})
    assert len(PydanticItem.__fields__) == 2
    assert "category" in PydanticItem.__fields__
    assert "id" not in PydanticItem.__fields__
    PydanticCategory = PydanticItem.__fields__["category"].type_
    assert len(PydanticCategory.__fields__) == 1
    assert "name" not in PydanticCategory.__fields__
