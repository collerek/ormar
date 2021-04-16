import json
from typing import List, Optional

import databases
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)
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


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Author(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Post(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories = ormar.ManyToMany(Category, skip_reverse=True)
    author: Optional[Author] = ormar.ForeignKey(Author, skip_reverse=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    await category.save_related(follow=True, save_all=True)
    return category


@app.post("/posts/", response_model=Post)
async def create_post(post: Post):
    if post.author:
        await post.author.save()
    await post.save()
    await post.save_related(follow=True, save_all=True)
    for category in [cat for cat in post.categories]:
        await post.categories.add(category)
    return post


@app.get("/categories/", response_model=List[Category])
async def get_categories():
    return await Category.objects.select_related("posts").all()


@app.get("/posts/", response_model=List[Post])
async def get_posts():
    posts = await Post.objects.select_related(["categories", "author"]).all()
    return posts


def test_queries():
    client = TestClient(app)
    with client as client:
        right_category = {"name": "Test category"}
        wrong_category = {"name": "Test category2", "posts": [{"title": "Test Post"}]}

        # cannot add posts if skipped, will be ignored (with extra=ignore by default)
        response = client.post("/categories/", data=json.dumps(wrong_category))
        assert response.status_code == 200
        response = client.get("/categories/")
        assert response.status_code == 200
        assert not "posts" in response.json()
        categories = [Category(**x) for x in response.json()]
        assert categories[0] is not None
        assert categories[0].name == "Test category2"

        response = client.post("/categories/", data=json.dumps(right_category))
        assert response.status_code == 200

        response = client.get("/categories/")
        assert response.status_code == 200
        categories = [Category(**x) for x in response.json()]
        assert categories[1] is not None
        assert categories[1].name == "Test category"

        right_post = {
            "title": "ok post",
            "author": {"first_name": "John", "last_name": "Smith"},
            "categories": [{"name": "New cat"}],
        }
        response = client.post("/posts/", data=json.dumps(right_post))
        assert response.status_code == 200

        Category.__config__.extra = "allow"
        response = client.get("/posts/")
        assert response.status_code == 200
        posts = [Post(**x) for x in response.json()]
        assert posts[0].title == "ok post"
        assert posts[0].author.first_name == "John"
        assert posts[0].categories[0].name == "New cat"

        wrong_category = {"name": "Test category3", "posts": [{"title": "Test Post"}]}

        # cannot add posts if skipped, will be error with extra forbid
        Category.__config__.extra = "forbid"
        response = client.post("/categories/", data=json.dumps(wrong_category))
        assert response.status_code == 422
