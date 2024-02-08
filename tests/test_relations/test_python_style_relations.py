from typing import List, Optional

import ormar
import pytest
import pytest_asyncio

from tests.settings import create_config
from tests.lifespan import init_tests


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


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="posts")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories: Optional[List[Category]] = ormar.ManyToMany(Category)
    author: Optional[Author] = ormar.ForeignKey(Author, related_name="author_posts")


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


@pytest.mark.asyncio
async def test_selecting_related(cleanup):
    async with base_ormar_config.database:
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
