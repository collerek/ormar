from typing import Optional

import sqlalchemy

import ormar
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///relations_docs002.db"

ormar_base_config = ormar.OrmarConfig(
    database=DatabaseConnection(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Author(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Post(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="posts")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories: Optional[list[Category]] = ormar.ManyToMany(Category)
    author: Optional[Author] = ormar.ForeignKey(Author)
