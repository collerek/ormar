# type: ignore

import databases
import pytest
import sqlalchemy

import ormar
from ormar import ModelDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


def test_through_with_relation_fails():
    class BaseMeta(ormar.ModelMeta):
        database = database
        metadata = metadata

    class Category(ormar.Model):
        class Meta(BaseMeta):
            tablename = "categories"

        id = ormar.Integer(primary_key=True)
        name = ormar.String(max_length=40)

    class Blog(ormar.Model):
        class Meta(BaseMeta):
            pass

        id: int = ormar.Integer(primary_key=True)
        title: str = ormar.String(max_length=200)

    class PostCategory(ormar.Model):
        class Meta(BaseMeta):
            tablename = "posts_x_categories"

        id: int = ormar.Integer(primary_key=True)
        sort_order: int = ormar.Integer(nullable=True)
        param_name: str = ormar.String(default="Name", max_length=200)
        blog = ormar.ForeignKey(Blog)

    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            class Meta(BaseMeta):
                pass

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories = ormar.ManyToMany(Category, through=PostCategory)
