import asyncio
from typing import List, Optional, Union

import databases
import pytest
import sqlalchemy

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Subject(ormar.Model):
    class Meta:
        tablename = "subjects"
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=80)


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
    sort_order: int = ormar.Integer(nullable=True)
    subject: Optional[Subject] = ormar.ForeignKey(Subject)


class PostCategory(ormar.Model):
    class Meta:
        tablename = "posts_categories"
        database = database
        metadata = metadata


class Post(ormar.Model):
    class Meta:
        tablename = "posts"
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories: Optional[Union[Category, List[Category]]] = ormar.ManyToMany(
        Category, through=PostCategory
    )
    author: Optional[Author] = ormar.ForeignKey(Author)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_queryset_methods():
    async with database:
        async with database.transaction(force_rollback=True):
            guido = await Author.objects.create(
                first_name="Guido", last_name="Van Rossum"
            )
            subject = await Subject(name="Random").save()
            post = await Post.objects.create(title="Hello, M2M", author=guido)
            news = await Category.objects.create(
                name="News", sort_order=1, subject=subject
            )
            breaking = await Category.objects.create(
                name="Breaking", sort_order=3, subject=subject
            )

            # Add a category to a post.
            await post.categories.add(news)
            await post.categories.add(breaking)

            category, created = await post.categories.get_or_create(name="News")
            assert category == news
            assert len(post.categories) == 1
            assert created is False

            category, created = await post.categories.get_or_create(
                name="Breaking News"
            )
            assert category != breaking
            assert category.pk is not None
            assert len(post.categories) == 2
            assert created is True

            await post.categories.update_or_create(pk=category.pk, name="Urgent News")
            assert len(post.categories) == 2
            cat, created = await post.categories.get_or_create(name="Urgent News")
            assert cat.pk == category.pk
            assert len(post.categories) == 1
            assert created is False

            await post.categories.remove(cat)
            await cat.delete()

            assert len(post.categories) == 0

            category = await post.categories.update_or_create(
                name="Weather News", sort_order=2, subject=subject
            )
            assert category.pk is not None
            assert category.posts[0] == post

            assert len(post.categories) == 1

            categories = await post.categories.all()
            assert len(categories) == 3 == len(post.categories)

            assert await post.categories.exists()
            assert 3 == await post.categories.count()

            categories = await post.categories.limit(2).all()
            assert len(categories) == 2 == len(post.categories)

            categories2 = await post.categories.limit(2).offset(1).all()
            assert len(categories2) == 2 == len(post.categories)
            assert categories != categories2

            categories = await post.categories.order_by("-sort_order").all()
            assert len(categories) == 3 == len(post.categories)
            assert post.categories[2].name == "News"
            assert post.categories[0].name == "Breaking"

            categories = await post.categories.exclude(name__icontains="news").all()
            assert len(categories) == 1 == len(post.categories)
            assert post.categories[0].name == "Breaking"

            categories = (
                await post.categories.filter(name__icontains="news")
                .order_by("-name")
                .all()
            )
            assert len(categories) == 2 == len(post.categories)
            assert post.categories[0].name == "Weather News"
            assert post.categories[1].name == "News"

            categories = await post.categories.fields("name").all()
            assert len(categories) == 3 == len(post.categories)
            for cat in post.categories:
                assert cat.sort_order is None

            categories = await post.categories.exclude_fields("sort_order").all()
            assert len(categories) == 3 == len(post.categories)
            for cat in post.categories:
                assert cat.sort_order is None
                assert cat.subject.name is None

            categories = await post.categories.select_related("subject").all()
            assert len(categories) == 3 == len(post.categories)
            for cat in post.categories:
                assert cat.subject.name is not None

            categories = await post.categories.prefetch_related("subject").all()
            assert len(categories) == 3 == len(post.categories)
            for cat in post.categories:
                assert cat.subject.name is not None


@pytest.mark.asyncio
async def test_queryset_update():
    async with database:
        async with database.transaction(force_rollback=True):
            guido = await Author.objects.create(
                first_name="Guido", last_name="Van Rossum"
            )
            subject = await Subject(name="Random").save()
            post = await Post.objects.create(title="Hello, M2M", author=guido)
            await post.categories.create(name="News", sort_order=1, subject=subject)
            await post.categories.create(name="Breaking", sort_order=3, subject=subject)

            await post.categories.order_by("sort_order").all()
            assert len(post.categories) == 2
            assert post.categories[0].sort_order == 1
            assert post.categories[0].name == "News"
            assert post.categories[1].sort_order == 3
            assert post.categories[1].name == "Breaking"

            updated = await post.categories.update(each=True, name="Test")
            assert updated == 2

            await post.categories.order_by("sort_order").all()
            assert len(post.categories) == 2
            assert post.categories[0].name == "Test"
            assert post.categories[1].name == "Test"

            updated = await post.categories.filter(sort_order=3).update(name="Test 2")
            assert updated == 1

            await post.categories.order_by("sort_order").all()
            assert len(post.categories) == 2
            assert post.categories[0].name == "Test"
            assert post.categories[1].name == "Test 2"

            with pytest.raises(QueryDefinitionError):
                await post.categories.update(name="Test WRONG")
