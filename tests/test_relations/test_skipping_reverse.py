from typing import List, Optional

import ormar
import pytest
import pytest_asyncio

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories: Optional[List[Category]] = ormar.ManyToMany(Category, skip_reverse=True)
    author: Optional[Author] = ormar.ForeignKey(Author, skip_reverse=True)


create_test_database = init_tests(base_ormar_config)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with base_ormar_config.database:
        PostCategory = Post.ormar_config.model_fields["categories"].through
        await PostCategory.objects.delete(each=True)
        await Post.objects.delete(each=True)
        await Category.objects.delete(each=True)
        await Author.objects.delete(each=True)


def test_model_definition():
    category = Category(name="Test")
    author = Author(first_name="Test", last_name="Author")
    post = Post(title="Test Post", author=author)
    post.categories = category

    assert post.categories[0] == category
    assert post.author == author

    with pytest.raises(AttributeError):
        assert author.posts

    with pytest.raises(AttributeError):
        assert category.posts

    assert "posts" not in category._orm


@pytest.mark.asyncio
async def test_assigning_related_objects(cleanup):
    async with base_ormar_config.database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")

        # Add a category to a post.
        await post.categories.add(news)
        # other way is disabled
        with pytest.raises(AttributeError):
            await news.posts.add(post)

        assert await post.categories.get_or_none(name="no exist") is None
        assert await post.categories.get_or_none(name="News") == news

        # Creating columns object from instance:
        await post.categories.create(name="Tips")
        assert len(post.categories) == 2

        post_categories = await post.categories.all()
        assert len(post_categories) == 2

        category = await Category.objects.select_related("posts").get(name="News")
        with pytest.raises(AttributeError):
            assert category.posts


@pytest.mark.asyncio
async def test_quering_of_related_model_works_but_no_result(cleanup):
    async with base_ormar_config.database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")

        await post.categories.add(news)

        post_categories = await post.categories.all()
        assert len(post_categories) == 1

        assert "posts" not in post.model_dump().get("categories", [])[0]

        assert news == await post.categories.get(name="News")

        posts_about_python = await Post.objects.filter(categories__name="python").all()
        assert len(posts_about_python) == 0

        # relation not in dict
        category = (
            await Category.objects.select_related("posts")
            .filter(posts__author=guido)
            .get()
        )
        assert category == news
        assert "posts" not in category.model_dump()

        # relation not in json
        category2 = (
            await Category.objects.select_related("posts")
            .filter(posts__author__first_name="Guido")
            .get()
        )
        assert category2 == news
        assert "posts" not in category2.model_dump_json()

        assert "posts" not in Category.model_json_schema().get("properties")


@pytest.mark.asyncio
async def test_removal_of_the_relations(cleanup):
    async with base_ormar_config.database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")
        await post.categories.add(news)
        assert len(await post.categories.all()) == 1
        await post.categories.remove(news)
        assert len(await post.categories.all()) == 0

        with pytest.raises(AttributeError):
            await news.posts.add(post)
        with pytest.raises(AttributeError):
            await news.posts.remove(post)

        await post.categories.add(news)
        await post.categories.clear()
        assert len(await post.categories.all()) == 0

        await post.categories.add(news)
        await news.delete()
        assert len(await post.categories.all()) == 0


@pytest.mark.asyncio
async def test_selecting_related(cleanup):
    async with base_ormar_config.database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        guido2 = await Author.objects.create(
            first_name="Guido2", last_name="Van Rossum"
        )

        post = await Post.objects.create(title="Hello, M2M", author=guido)
        post2 = await Post.objects.create(title="Bye, M2M", author=guido2)

        news = await Category.objects.create(name="News")
        recent = await Category.objects.create(name="Recent")

        await post.categories.add(news)
        await post.categories.add(recent)
        await post2.categories.add(recent)

        assert len(await post.categories.all()) == 2
        assert (await post.categories.limit(1).all())[0] == news
        assert (await post.categories.offset(1).limit(1).all())[0] == recent
        assert await post.categories.first() == news
        assert await post.categories.exists()

        # still can order
        categories = (
            await Category.objects.select_related("posts")
            .order_by("posts__title")
            .all()
        )
        assert categories[0].name == "Recent"
        assert categories[1].name == "News"

        # still can filter
        categories = await Category.objects.filter(posts__title="Bye, M2M").all()
        assert categories[0].name == "Recent"
        assert len(categories) == 1

        # same for reverse fk
        authors = (
            await Author.objects.select_related("posts").order_by("posts__title").all()
        )
        assert authors[0].first_name == "Guido2"
        assert authors[1].first_name == "Guido"

        authors = await Author.objects.filter(posts__title="Bye, M2M").all()
        assert authors[0].first_name == "Guido2"
        assert len(authors) == 1
