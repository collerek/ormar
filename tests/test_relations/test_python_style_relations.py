from typing import List, Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
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
    author: Optional[Author] = ormar.ForeignKey(Author, related_name="author_posts")


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
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
        categories = await Category.objects.select_related(Category.posts).all()
        assert len(categories) == 2
        assert categories[0].name == "News"

        news_posts = await news.posts.select_related(Post.author).all()
        assert news_posts[0].author == guido
        assert (await post.categories.limit(1).all())[0] == news
        assert (await post.categories.offset(1).limit(1).all())[0] == recent
        assert await post.categories.first() == news
        assert await post.categories.exists()

        author = await Author.objects.prefetch_related(
            Author.author_posts.categories
        ).get()
        assert len(author.author_posts) == 1
        assert author.author_posts[0].title == "Hello, M2M"
        assert author.author_posts[0].categories[0].name == "News"
        assert author.author_posts[0].categories[1].name == "Recent"

        post = await Post.objects.select_related([Post.author, Post.categories]).get()
        assert len(post.categories) == 2
        assert post.categories[0].name == "News"
        assert post.categories[1].name == "Recent"
        assert post.author.first_name == "Guido"
