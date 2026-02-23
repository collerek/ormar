from typing import Optional

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))
headers = {"content-type": "application/json"}


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Category2(Category):
    model_config = dict(extra="forbid")


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories = ormar.ManyToMany(Category, skip_reverse=True)
    author: Optional[Author] = ormar.ForeignKey(Author, skip_reverse=True)


create_test_database = init_tests(base_ormar_config)


@app.post("/categories/forbid/", response_model=Category2)
async def create_category_forbid(category: Category2):  # pragma: no cover
    pass


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


@app.get("/categories/", response_model=list[Category])
async def get_categories():
    return await Category.objects.select_related("posts").all()


@app.get("/posts/", response_model=list[Post])
async def get_posts():
    posts = await Post.objects.select_related(["categories", "author"]).all()
    return posts


@pytest.mark.asyncio
async def test_queries():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        right_category = {"name": "Test category"}
        wrong_category = {"name": "Test category2", "posts": [{"title": "Test Post"}]}

        # cannot add posts if skipped, will be ignored (with extra=ignore by default)
        response = await client.post(
            "/categories/", json=wrong_category, headers=headers
        )
        assert response.status_code == 200
        response = await client.get("/categories/")
        assert response.status_code == 200
        assert "posts" not in response.json()
        categories = [Category(**x) for x in response.json()]
        assert categories[0] is not None
        assert categories[0].name == "Test category2"

        response = await client.post(
            "/categories/", json=right_category, headers=headers
        )
        assert response.status_code == 200

        response = await client.get("/categories/")
        assert response.status_code == 200
        categories = [Category(**x) for x in response.json()]
        assert categories[1] is not None
        assert categories[1].name == "Test category"

        right_post = {
            "title": "ok post",
            "author": {"first_name": "John", "last_name": "Smith"},
            "categories": [{"name": "New cat"}],
        }
        response = await client.post("/posts/", json=right_post, headers=headers)
        assert response.status_code == 200

        Category.model_config["extra"] = "allow"
        response = await client.get("/posts/")
        assert response.status_code == 200
        posts = [Post(**x) for x in response.json()]
        assert posts[0].title == "ok post"
        assert posts[0].author.first_name == "John"
        assert posts[0].categories[0].name == "New cat"

        wrong_category = {"name": "Test category3", "posts": [{"title": "Test Post"}]}

        # cannot add posts if skipped, will be error with extra forbid
        assert Category2.model_config["extra"] == "forbid"
        response = await client.post("/categories/forbid/", json=wrong_category)
        assert response.status_code == 422
