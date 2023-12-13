# type: ignore
from typing import List, Optional

import databases
import pytest
import sqlalchemy

import ormar
from ormar.exceptions import ModelDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Author(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "authors",
        database = database,
        metadata = metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "categories",
        database = database,
        metadata = metadata,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


def test_fk_error():
    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            ormar_config = ormar.OrmarConfig(
                tablename = "posts",
                database = database,
                metadata = metadata,
            )

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories: Optional[List[Category]] = ormar.ManyToMany(Category)
            author: Optional[Author] = ormar.ForeignKey(Author, default="aa")


def test_m2m_error():
    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            ormar_config = ormar.OrmarConfig(
                tablename = "posts",
                database = database,
                metadata = metadata,
            )

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories: Optional[List[Category]] = ormar.ManyToMany(
                Category, default="aa"
            )
