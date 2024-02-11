# type: ignore

import ormar
import pytest
from ormar import ModelDefinitionError

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


def test_through_with_relation_fails():
    class Category(ormar.Model):
        ormar_config = base_ormar_config.copy(tablename="categories")

        id = ormar.Integer(primary_key=True)
        name = ormar.String(max_length=40)

    class Blog(ormar.Model):
        ormar_config = base_ormar_config.copy()

        id: int = ormar.Integer(primary_key=True)
        title: str = ormar.String(max_length=200)

    class PostCategory(ormar.Model):
        ormar_config = base_ormar_config.copy(tablename="posts_x_categories")

        id: int = ormar.Integer(primary_key=True)
        sort_order: int = ormar.Integer(nullable=True)
        param_name: str = ormar.String(default="Name", max_length=200)
        blog = ormar.ForeignKey(Blog)

    with pytest.raises(ModelDefinitionError):

        class Post(ormar.Model):
            ormar_config = base_ormar_config.copy()

            id: int = ormar.Integer(primary_key=True)
            title: str = ormar.String(max_length=200)
            categories = ormar.ManyToMany(Category, through=PostCategory)


create_test_database = init_tests(base_ormar_config)
