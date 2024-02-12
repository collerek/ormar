# type: ignore
from typing import List, Optional

import ormar
import pytest
from ormar.exceptions import ModelDefinitionError

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


create_test_database = init_tests(base_ormar_config)


def test_fk_error():
    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            ormar_config = base_ormar_config.copy(tablename="posts")

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories: Optional[List[Category]] = ormar.ManyToMany(Category)
            author: Optional[Author] = ormar.ForeignKey(Author, default="aa")


def test_m2m_error():
    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            ormar_config = base_ormar_config.copy(tablename="posts")

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories: Optional[List[Category]] = ormar.ManyToMany(
                Category, default="aa"
            )
