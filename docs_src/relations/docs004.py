import ormar
import sqlalchemy
from ormar import DatabaseConnection

DATABASE_URL = "sqlite+aiosqlite:///relations_docs004.db"

ormar_base_config = ormar.OrmarConfig(
    database=DatabaseConnection(DATABASE_URL), metadata=sqlalchemy.MetaData()
)


class Category(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="categories")

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=40)


class PostCategory(ormar.Model):
    ormar_config = ormar_base_config.copy(tablename="posts_x_categories")

    id: int = ormar.Integer(primary_key=True)
    sort_order: int = ormar.Integer(nullable=True)
    param_name: str = ormar.String(default="Name", max_length=200)


class Post(ormar.Model):
    ormar_config = ormar_base_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories = ormar.ManyToMany(Category, through=PostCategory)
