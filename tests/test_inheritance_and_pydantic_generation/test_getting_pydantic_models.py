from typing import List, Optional

import databases
import pydantic
import sqlalchemy
from pydantic import ConstrainedStr, PositiveInt
from pydantic.typing import ForwardRef

import ormar
from ormar.fields.foreign_key import ForeignKey
from tests.settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class SelfRef(ormar.Model):
    class Meta(BaseMeta):
        tablename = "self_refs"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="selfref")
    parent = ormar.ForeignKey(ForwardRef("SelfRef"), related_name="children")


SelfRef.update_forward_refs()


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, default="test")
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)


class OrderPosition(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    item: Optional[Item] = ormar.ForeignKey(Item, skip_reverse=True)


class Order(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    position: Optional[OrderPosition] = ForeignKey(OrderPosition)


class MutualA(ormar.Model):
    class Meta(BaseMeta):
        tablename = "mutual_a"

    id: int = ormar.Integer(primary_key=True)
    mutual_b = ormar.ForeignKey(ForwardRef("MutualB"), related_name="mutuals_a")


class MutualB(ormar.Model):
    class Meta(BaseMeta):
        tablename = "mutual_b"

    id: int = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100, default="test")
    mutual_a = ormar.ForeignKey(MutualA, related_name="mutuals_b")


MutualA.update_forward_refs()


def test_getting_pydantic_model():
    PydanticCategory = Category.get_pydantic()
    assert issubclass(PydanticCategory, pydantic.BaseModel)
    assert {*PydanticCategory.__fields__.keys()} == {"items", "id", "name"}

    assert not PydanticCategory.__fields__["id"].required
    assert PydanticCategory.__fields__["id"].outer_type_ == int
    assert PydanticCategory.__fields__["id"].default is None

    assert PydanticCategory.__fields__["name"].required
    assert issubclass(PydanticCategory.__fields__["name"].outer_type_, ConstrainedStr)
    assert PydanticCategory.__fields__["name"].default in [None, Ellipsis]

    PydanticItem = PydanticCategory.__fields__["items"].type_
    assert PydanticCategory.__fields__["items"].outer_type_ == List[PydanticItem]
    assert issubclass(PydanticItem, pydantic.BaseModel)
    assert not PydanticItem.__fields__["name"].required
    assert PydanticItem.__fields__["name"].default == "test"
    assert issubclass(PydanticItem.__fields__["name"].outer_type_, ConstrainedStr)
    assert "category" not in PydanticItem.__fields__


def test_initializing_pydantic_model():
    data = {
        "id": 1,
        "name": "test",
        "items": [{"id": 1, "name": "test_i1"}, {"id": 2, "name": "test_i2"}],
    }
    PydanticCategory = Category.get_pydantic()
    cat = PydanticCategory(**data)
    assert cat.dict() == data

    data = {"id": 1, "name": "test"}
    cat = PydanticCategory(**data)
    assert cat.dict() == {**data, "items": None}


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


def test_getting_pydantic_model_fk_as_int():
    PydanticItem = Item.get_pydantic(
        include={"category", "name"}, fk_as_int={"category", "name"}
    )
    assert len(PydanticItem.__fields__) == 2
    assert PydanticItem.__fields__["category"].type_ == PositiveInt
    assert PydanticItem.__fields__["name"].type_ != PositiveInt


def test_getting_pydantic_model_nested_fk_as_int():
    PydanticOrder = Order.get_pydantic(
        include={"name", "position"}, fk_as_int={"position__item"}
    )
    assert len(PydanticOrder.__fields__) == 2
    PydanticPosition = PydanticOrder.__fields__["position"].type_
    assert len(PydanticPosition.__fields__) == 3
    assert PydanticPosition.__fields__["item"].type_ == PositiveInt


def test_getting_pydantic_model_self_ref():
    PydanticSelfRef = SelfRef.get_pydantic()
    assert len(PydanticSelfRef.__fields__) == 4
    assert set(PydanticSelfRef.__fields__.keys()) == {
        "id",
        "name",
        "parent",
        "children",
    }
    InnerSelf = PydanticSelfRef.__fields__["parent"].type_
    assert len(InnerSelf.__fields__) == 2
    assert set(InnerSelf.__fields__.keys()) == {"id", "name"}

    InnerSelf2 = PydanticSelfRef.__fields__["children"].type_
    assert len(InnerSelf2.__fields__) == 2
    assert set(InnerSelf2.__fields__.keys()) == {"id", "name"}


def test_getting_pydantic_model_self_ref_exclude():
    PydanticSelfRef = SelfRef.get_pydantic(exclude={"children": {"name"}})
    assert len(PydanticSelfRef.__fields__) == 4
    assert set(PydanticSelfRef.__fields__.keys()) == {
        "id",
        "name",
        "parent",
        "children",
    }

    InnerSelf = PydanticSelfRef.__fields__["parent"].type_
    assert len(InnerSelf.__fields__) == 2
    assert set(InnerSelf.__fields__.keys()) == {"id", "name"}

    PydanticSelfRefChildren = PydanticSelfRef.__fields__["children"].type_
    assert len(PydanticSelfRefChildren.__fields__) == 1
    assert set(PydanticSelfRefChildren.__fields__.keys()) == {"id"}
    assert PydanticSelfRef != PydanticSelfRefChildren
    assert InnerSelf != PydanticSelfRefChildren


def test_getting_pydantic_model_mutual_rels():
    MutualAPydantic = MutualA.get_pydantic()
    assert len(MutualAPydantic.__fields__) == 3
    assert set(MutualAPydantic.__fields__.keys()) == {"id", "mutual_b", "mutuals_b"}

    MutualB1 = MutualAPydantic.__fields__["mutual_b"].type_
    MutualB2 = MutualAPydantic.__fields__["mutuals_b"].type_
    assert len(MutualB1.__fields__) == 2
    assert set(MutualB1.__fields__.keys()) == {"id", "name"}
    assert len(MutualB2.__fields__) == 2
    assert set(MutualB2.__fields__.keys()) == {"id", "name"}
    assert MutualB1 == MutualB2


def test_getting_pydantic_model_mutual_rels_exclude():
    MutualAPydantic = MutualA.get_pydantic(exclude={"mutual_b": {"name"}})
    assert len(MutualAPydantic.__fields__) == 3
    assert set(MutualAPydantic.__fields__.keys()) == {"id", "mutual_b", "mutuals_b"}

    MutualB1 = MutualAPydantic.__fields__["mutual_b"].type_
    MutualB2 = MutualAPydantic.__fields__["mutuals_b"].type_

    assert len(MutualB1.__fields__) == 1
    assert set(MutualB1.__fields__.keys()) == {"id"}
    assert len(MutualB2.__fields__) == 2
    assert set(MutualB2.__fields__.keys()) == {"id", "name"}
    assert MutualB1 != MutualB2
