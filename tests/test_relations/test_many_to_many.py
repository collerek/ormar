import asyncio
from typing import List, Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from ormar.exceptions import ModelPersistenceError, NoMatch, RelationshipInstanceError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Author(ormar.Model):
    class Meta:
        tablename = "authors"
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Post(ormar.Model):
    class Meta:
        tablename = "posts"
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories: Optional[List[Category]] = ormar.ManyToMany(Category)
    author: Optional[Author] = ormar.ForeignKey(Author)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="module")
async def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with database:
        PostCategory = Post.Meta.model_fields["categories"].through
        await PostCategory.objects.delete(each=True)
        await Post.objects.delete(each=True)
        await Category.objects.delete(each=True)
        await Author.objects.delete(each=True)


@pytest.mark.asyncio
async def test_not_saved_raises_error(cleanup):
    async with database:
        guido = await Author(first_name="Guido", last_name="Van Rossum").save()
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = Category(name="News")

        with pytest.raises(ModelPersistenceError):
            await post.categories.add(news)


@pytest.mark.asyncio
async def test_not_existing_raises_error(cleanup):
    async with database:
        guido = await Author(first_name="Guido", last_name="Van Rossum").save()
        post = await Post.objects.create(title="Hello, M2M", author=guido)

        with pytest.raises(NoMatch):
            await post.categories.get()

        assert await post.categories.get_or_none() is None


@pytest.mark.asyncio
async def test_assigning_related_objects(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")

        # Add a category to a post.
        await post.categories.add(news)
        # or from the other end:
        await news.posts.add(post)

        assert await post.categories.get_or_none(name="no exist") is None
        assert await post.categories.get_or_none(name="News") == news

        # Creating columns object from instance:
        await post.categories.create(name="Tips")
        assert len(post.categories) == 2

        post_categories = await post.categories.all()
        assert len(post_categories) == 2


@pytest.mark.asyncio
async def test_quering_of_the_m2m_models(cleanup):
    async with database:
        # orm can do this already.
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")
        # tl;dr: `post.categories` exposes the QuerySet API.

        await post.categories.add(news)

        post_categories = await post.categories.all()
        assert len(post_categories) == 1

        assert news == await post.categories.get(name="News")

        num_posts = await news.posts.count()
        assert num_posts == 1

        posts_about_m2m = await news.posts.filter(title__contains="M2M").all()
        assert len(posts_about_m2m) == 1
        assert posts_about_m2m[0] == post
        posts_about_python = await Post.objects.filter(categories__name="python").all()
        assert len(posts_about_python) == 0

        # Traversal of relationships: which categories has Guido contributed to?
        category = await Category.objects.filter(posts__author=guido).get()
        assert category == news
        # or:
        category2 = await Category.objects.filter(
            posts__author__first_name="Guido"
        ).get()
        assert category2 == news


@pytest.mark.asyncio
async def test_removal_of_the_relations(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")
        await post.categories.add(news)
        assert len(await post.categories.all()) == 1
        await post.categories.remove(news)
        assert len(await post.categories.all()) == 0
        # or:
        await news.posts.add(post)
        assert len(await news.posts.all()) == 1
        await news.posts.remove(post)
        assert len(await news.posts.all()) == 0

        # Remove all columns objects:
        await post.categories.add(news)
        await post.categories.clear()
        assert len(await post.categories.all()) == 0

        # post would also lose 'news' category when running:
        await post.categories.add(news)
        await news.delete()
        assert len(await post.categories.all()) == 0


@pytest.mark.asyncio
async def test_selecting_related(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = await Category.objects.create(name="News")
        recent = await Category.objects.create(name="Recent")
        await post.categories.add(news)
        await post.categories.add(recent)
        assert len(await post.categories.all()) == 2
        # Loads categories and posts (2 queries) and perform the join in Python.
        categories = await Category.objects.select_related("posts").all()
        # No extra queries needed => no more `await`s required.
        for category in categories:
            assert category.posts[0] == post

        news_posts = await news.posts.select_related("author").all()
        assert news_posts[0].author == guido

        assert (await post.categories.limit(1).all())[0] == news
        assert (await post.categories.offset(1).limit(1).all())[0] == recent

        assert await post.categories.first() == news

        assert await post.categories.exists()


@pytest.mark.asyncio
async def test_selecting_related_fail_without_saving(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = Post(title="Hello, M2M", author=guido)
        with pytest.raises(RelationshipInstanceError):
            await post.categories.all()


@pytest.mark.asyncio
async def test_adding_unsaved_related(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = Category(name="News")
        with pytest.raises(ModelPersistenceError):
            await post.categories.add(news)

        await news.save()
        await post.categories.add(news)
        assert len(await post.categories.all()) == 1


@pytest.mark.asyncio
async def test_removing_unsaved_related(cleanup):
    async with database:
        guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
        post = await Post.objects.create(title="Hello, M2M", author=guido)
        news = Category(name="News")
        with pytest.raises(NoMatch):
            await post.categories.remove(news)
