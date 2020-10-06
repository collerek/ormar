# ORMar
<p>
<a href="https://pypi.org/project/ormar">
    <img src="https://img.shields.io/pypi/v/ormar.svg" alt="Pypi version">
</a>
<a href="https://pypi.org/project/ormar">
    <img src="https://img.shields.io/pypi/pyversions/ormar.svg" alt="Pypi version">
</a>
<a href="https://travis-ci.com/collerek/ormar">
    <img src="https://travis-ci.com/collerek/ormar.svg?branch=master" alt="Build Status">
</a>
<a href="https://codecov.io/gh/collerek/ormar">
    <img src="https://codecov.io/gh/collerek/ormar/branch/master/graph/badge.svg" alt="Coverage">
</a>
<a href="https://www.codefactor.io/repository/github/collerek/ormar">
<img src="https://www.codefactor.io/repository/github/collerek/ormar/badge" alt="CodeFactor" />
</a>
<a href="https://app.codacy.com/manual/collerek/ormar?utm_source=github.com&utm_medium=referral&utm_content=collerek/oramr&utm_campaign=Badge_Grade_Dashboard">
<img src="https://api.codacy.com/project/badge/Grade/62568734f70f49cd8ea7a1a0b2d0c107" alt="Codacy" />
</a>
</p>

The `ormar` package is an async ORM for Python, with support for Postgres,
MySQL, and SQLite. 

Ormar - apart form obvious ORM in name - get it's name from ormar in swedish which means snakes, and ormar(e) in italian which means cabinet. 
And what's a better name for python ORM than snakes cabinet :)

Ormar is built with:

  * [`SQLAlchemy core`][sqlalchemy-core] for query building.
  * [`databases`][databases] for cross-database async support.
  * [`pydantic`][pydantic] for data validation.

Because ormar is built on SQLAlchemy core, you can use [`alembic`][alembic] to provide
database migrations.

The goal was to create a simple ORM that can be used directly (as request and response models) with [`fastapi`][fastapi] that bases it's data validation on pydantic.
Initial work was inspired by [`encode/orm`][encode/orm], later I found `ormantic` and used it as a further inspiration.
The encode package was too simple (i.e. no ability to join two times to the same table) and used typesystem for data checks.


**ormar is still under development:** We recommend pinning any dependencies with `ormar~=0.2.0`

**Note**: Use `ipython` to try this from the console, since it supports `await`.

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Note(ormar.Model):
    class Meta:
        tablename = "notes"
        database = database
        metadata = metadata

    # primary keys of type int by dafault are set to autoincrement    
    id: ormar.Integer(primary_key=True)
    text: ormar.String(length=100)
    completed: ormar.Boolean(default=False)
    # as of ormar >=0.3.2 you can provide a list of choices that will be validated
    flag: ormar.String(default='To do', choices=['To do', 'Pending', 'Done'])

# Create the database
engine = sqlalchemy.create_engine(str(database.url))
metadata.create_all(engine)

# .create()
await Note.objects.create(text="Buy the groceries.", completed=False)
await Note.objects.create(text="Call Mum.", completed=True)
await Note.objects.create(text="Send invoices.", completed=True)

# .all()
notes = await Note.objects.all()

# .filter()
notes = await Note.objects.filter(completed=True).all()

# exact, iexact, contains, icontains, lt, lte, gt, gte, in
notes = await Note.objects.filter(text__icontains="mum").all()

# exclude - from ormar >= 0.3.1
notes = await Note.objects.exclude(text__icontains="mum").all()

# startswith, istartswith, endswith, iendswith - from ormar >= 0.3.3
notes = await Note.objects.filter(text__iendswith="mum.").all()
notes = await Note.objects.filter(text__istartswith="call").all()
notes = await Note.objects.filter(text__startswith="Buy").all()

# .get()
note = await Note.objects.get(id=1)

# .update()
await note.update(completed=True)

# .delete()
await note.delete()

# 'pk' always refers to the primary key
note = await Note.objects.get(pk=2)
note.pk  # 2
```

Ormar supports loading and filtering across foreign keys...

```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    album: ormar.ForeignKey(Album)
    title: ormar.String(length=100)
    position: ormar.Integer()


# Create some records to work with.
malibu = await Album.objects.create(name="Malibu")
await Track.objects.create(album=malibu, title="The Bird", position=1)
await Track.objects.create(album=malibu, title="Heart don't stand a chance", position=2)
await Track.objects.create(album=malibu, title="The Waters", position=3)

fantasies = await Album.objects.create(name="Fantasies")
await Track.objects.create(album=fantasies, title="Help I'm Alive", position=1)
await Track.objects.create(album=fantasies, title="Sick Muse", position=2)


# Fetch an instance, without loading a foreign key relationship on it.
track = await Track.objects.get(title="The Bird")

# We have an album instance, but it only has the primary key populated
print(track.album)       # Album(id=1) [sparse]
print(track.album.pk)    # 1
print(track.album.name)  # Raises AttributeError

# Load the relationship from the database
await track.album.load()
assert track.album.name == "Malibu"

# This time, fetch an instance, loading the foreign key relationship.
track = await Track.objects.select_related("album").get(title="The Bird")
assert track.album.name == "Malibu"

# By default you also get a second side of the relation 
# constructed as lowercase source model name +'s' (tracks in this case)
# you can also provide custom name with parameter related_name
album = await Album.objects.select_related("tracks").all()
assert len(album.tracks) == 3

# Fetch instances, with a filter across an FK relationship.
tracks = Track.objects.filter(album__name="Fantasies")
assert len(tracks) == 2

# Fetch instances, with a filter and operator across an FK relationship.
tracks = Track.objects.filter(album__name__iexact="fantasies")
assert len(tracks) == 2

# Limit a query
tracks = await Track.objects.limit(1).all()
assert len(tracks) == 1
```

Since version >=0.3 Ormar supports also many to many relationships
```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Author(ormar.Model):
    class Meta:
        tablename = "authors"
        database = database
        metadata = metadata

    id: ormar.Integer(primary_key=True)
    first_name: ormar.String(max_length=80)
    last_name: ormar.String(max_length=80)


class Category(ormar.Model):
    class Meta:
        tablename = "categories"
        database = database
        metadata = metadata

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=40)


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

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    categories: ormar.ManyToMany(Category, through=PostCategory)
    author: ormar.ForeignKey(Author)

guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
post = await Post.objects.create(title="Hello, M2M", author=guido)
news = await Category.objects.create(name="News")

# Add a category to a post.
await post.categories.add(news)
# or from the other end:
await news.posts.add(post)

# Creating columns object from instance:
await post.categories.create(name="Tips")
assert len(await post.categories.all()) == 2

# Many to many relation exposes a list of columns models 
# and an API of the Queryset:
assert news == await post.categories.get(name="News")

# with all Queryset methods - filtering, selecting columns, counting etc.
await news.posts.filter(title__contains="M2M").all()
await Category.objects.filter(posts__author=guido).get()

# columns models of many to many relation can be prefetched
news_posts = await news.posts.select_related("author").all()
assert news_posts[0].author == guido

# Removal of the relationship by one
await news.posts.remove(post)
# or all at once
await news.posts.clear()

```

Since version >=0.3.4 Ormar supports also queryset level delete and update statements, 
as well as get_or_create and update_or_create
```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    author: ormar.String(max_length=100)
    genre: ormar.String(max_length=100, default='Fiction', choices=['Fiction', 'Adventure', 'Historic', 'Fantasy'])

await Book.objects.create(title='Tom Sawyer', author="Twain, Mark", genre='Adventure')
await Book.objects.create(title='War and Peace', author="Tolstoy, Leo", genre='Fiction')
await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')
await Book.objects.create(title='Harry Potter', author="Rowling, J.K.", genre='Fantasy')
await Book.objects.create(title='Lord of the Rings', author="Tolkien, J.R.", genre='Fantasy')

# update accepts kwargs that are used to update queryset model
# all other arguments are ignored (argument names not in own model table)
await Book.objects.filter(author="Tolstoy, Leo").update(author="Lenin, Vladimir") # update all Tolstoy's books
all_books = await Book.objects.filter(author="Lenin, Vladimir").all()
assert len(all_books) == 2

# delete accepts kwargs that will be used in filter
# acting in same way as queryset.filter(**kwargs).delete()
await Book.objects.delete(genre='Fantasy') # delete all fantasy books
all_books = await Book.objects.all()
assert len(all_books) == 3

# queryset needs to be filtered before deleting to prevent accidental overwrite
# to update whole database table each=True needs to be provided as a safety switch
await Book.objects.update(each=True, genre='Fiction')
all_books = await Book.objects.filter(genre='Fiction').all()
assert len(all_books) == 3

# helper get/update or create methods of queryset
# if not exists it will be created
vol1 = await Book.objects.get_or_create(title="Volume I", author='Anonymous', genre='Fiction')
assert await Book.objects.count() == 1

# if exists it will be returned
assert await Book.objects.get_or_create(title="Volume I", author='Anonymous', genre='Fiction') == vol1
assert await Book.objects.count() == 1

# if not exist the instance will be persisted in db
vol2 = await Book.objects.update_or_create(title="Volume II", author='Anonymous', genre='Fiction')
assert await Book.objects.count() == 1

# if pk or pkname passed in kwargs (like id here) the object will be updated
assert await Book.objects.update_or_create(id=vol2.id, genre='Historic')
assert await Book.objects.count() == 1

```


Since version >=0.3.5 Ormar supports also bulk operations -> bulk_create and bulk_update
```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class ToDo(ormar.Model):
    class Meta:
        tablename = "todos"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    text: ormar.String(max_length=500)
    completed: ormar.Boolean(default=False)

# create multiple instances at once with bulk_create
await ToDo.objects.bulk_create(
            [
                ToDo(text="Buy the groceries."),
                ToDo(text="Call Mum.", completed=True),
                ToDo(text="Send invoices.", completed=True),
            ]
        )

todoes = await ToDo.objects.all()
assert len(todoes) == 3

# update objects
for todo in todoes:
    todo.completed = False

# perform update of all objects at once
# objects need to have pk column set, otherwise exception is raised
await ToDo.objects.bulk_update(todoes)

completed = await ToDo.objects.filter(completed=False).all()
assert len(completed) == 3

```

Since version >=0.3.6 Ormar supports unique constraints on multiple columns
```python
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Product(ormar.Model):
    class Meta:
        tablename = "products"
        metadata = metadata
        database = database
        # define your constraints in Meta class of the model
        # it's a list that can contain multiple constraints
        constraints = [ormar.UniqueColumns("name", "company")]

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    company: ormar.String(max_length=200)

await Product.objects.create(name="Cookies", company="Nestle")
await Product.objects.create(name="Mars", company="Mars")
await Product.objects.create(name="Mars", company="Nestle")


# will raise error based on backend 
# (sqlite3.IntegrityError, pymysql.IntegrityError, asyncpg.exceptions.UniqueViolationError)
await Product.objects.create(name="Mars", company="Mars")       

```

Since version >=0.3.6 Ormar supports selecting subset of model columns to limit the data load.
Warning - mandatory fields cannot be excluded as it will raise validation error, to exclude a field it has to be nullable.
Pk column cannot be excluded - it's always auto added even if not explicitly included.
```python
import databases
import pydantic
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Company(ormar.Model):
    class Meta:
        tablename = "companies"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=100)
    founded: ormar.Integer(nullable=True)


class Car(ormar.Model):
    class Meta:
        tablename = "cars"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    manufacturer: ormar.ForeignKey(Company)
    name: ormar.String(max_length=100)
    year: ormar.Integer(nullable=True)
    gearbox_type: ormar.String(max_length=20, nullable=True)
    gears: ormar.Integer(nullable=True)
    aircon_type: ormar.String(max_length=20, nullable=True)



# build some sample data
toyota = await Company.objects.create(name="Toyota", founded=1937)
await Car.objects.create(manufacturer=toyota, name="Corolla", year=2020, gearbox_type='Manual', gears=5,
                         aircon_type='Manual')
await Car.objects.create(manufacturer=toyota, name="Yaris", year=2019, gearbox_type='Manual', gears=5,
                         aircon_type='Manual')
await Car.objects.create(manufacturer=toyota, name="Supreme", year=2020, gearbox_type='Auto', gears=6,
                         aircon_type='Auto')

# select manufacturer but only name - to include related models use notation {model_name}__{column}
all_cars = await Car.objects.select_related('manufacturer').fields(['id', 'name', 'company__name']).all()
for car in all_cars:
    # excluded columns will yield None
    assert all(getattr(car, x) is None for x in ['year', 'gearbox_type', 'gears', 'aircon_type'])
    # included column on related models will be available, pk column is always included
    # even if you do not include it in fields list
    assert car.manufacturer.name == 'Toyota'
    # also in the nested related models - you cannot exclude pk - it's always auto added 
    assert car.manufacturer.founded is None

# fields() can be called several times, building up the columns to select
# models selected in select_related but with no columns in fields list implies all fields
all_cars = await Car.objects.select_related('manufacturer').fields('id').fields(
                ['name']).all()
# all fiels from company model are selected
assert all_cars[0].manufacturer.name == 'Toyota' 
assert all_cars[0].manufacturer.founded ==  1937

# cannot exclude mandatory model columns - company__name in this example
await Car.objects.select_related('manufacturer').fields(['id', 'name', 'company__founded']).all()
# will raise pydantic ValidationError as company.name is required

```


## Data types

The following keyword arguments are supported on all field types.

  * `primary_key: bool`
  * `nullable: bool`
  * `default: Any`
  * `server_default: Any`
  * `index: bool`
  * `unique: bool`
  * `choices: typing.Sequence`

All fields are required unless one of the following is set:

  * `nullable` - Creates a nullable column. Sets the default to `None`.
  * `default` - Set a default value for the field.
  * `server_default` - Set a default value for the field on server side (like sqlalchemy's `func.now()`).
  * `primary key` with `autoincrement` - When a column is set to primary key and autoincrement is set on this column. 
Autoincrement is set by default on int primary keys. 

Available Model Fields (with required args - optional ones in docs):
* `String(max_length)`
* `Text()`
* `Boolean()`
* `Integer()`
* `Float()`
* `Date()`
* `Time()`
* `DateTime()`
* `JSON()`
* `BigInteger()`
* `Decimal(scale, precision)`
* `UUID()`
* `ForeignKey(to)`
* `Many2Many(to, through)`

[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[databases]: https://github.com/encode/databases
[pydantic]: https://pydantic-docs.helpmanual.io/
[encode/orm]: https://github.com/encode/orm/
[alembic]: https://alembic.sqlalchemy.org/en/latest/
[fastapi]: https://fastapi.tiangolo.com/