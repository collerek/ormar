from typing import Optional

import databases
import ormar
import pydantic
import sqlalchemy

DATABASE_URL = "sqlite:///db.sqlite"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


# note that this step is optional -> all ormar cares is a internal
# class with name Meta and proper parameters, but this way you do not
# have to repeat the same parameters if you use only one database
base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)

# Note that all type hints are optional
# below is a perfectly valid model declaration
# class Author(ormar.Model):
#     class Meta(BaseMeta):
#         tablename = "authors"
#
#     id = ormar.Integer(primary_key=True) # <= notice no field types
#     name = ormar.String(max_length=100)


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


# create the database
# note that in production you should use migrations
# note that this is not required if you connect to existing database
engine = sqlalchemy.create_engine(DATABASE_URL)
# just to be sure we clear the db before
metadata.drop_all(engine)
metadata.create_all(engine)


# all functions below are divided into functionality categories
# note how all functions are defined with async - hence can use await AND needs to
# be awaited on their own
async def create():
    # Create some records to work with through QuerySet.create method.
    # Note that queryset is exposed on each Model's class as objects
    tolkien = await Author.objects.create(name="J.R.R. Tolkien")
    await Book.objects.create(author=tolkien, title="The Hobbit", year=1937)
    await Book.objects.create(author=tolkien, title="The Lord of the Rings", year=1955)
    await Book.objects.create(author=tolkien, title="The Silmarillion", year=1977)

    # alternative creation of object divided into 2 steps
    sapkowski = Author(name="Andrzej Sapkowski")
    # do some stuff
    await sapkowski.save()

    # or save() after initialization
    await Book(author=sapkowski, title="The Witcher", year=1990).save()
    await Book(author=sapkowski, title="The Tower of Fools", year=2002).save()

    # to read more about inserting data into the database
    # visit: https://collerek.github.io/ormar/queries/create/


async def read():
    # Fetch an instance, without loading a foreign key relationship on it.
    # Django style
    book = await Book.objects.get(title="The Hobbit")
    # or python style
    book = await Book.objects.get(Book.title == "The Hobbit")
    book2 = await Book.objects.first()

    # first() fetch the instance with lower primary key value
    assert book == book2

    # you can access all fields on loaded model
    assert book.title == "The Hobbit"
    assert book.year == 1937

    # when no condition is passed to get()
    # it behaves as last() based on primary key column
    book3 = await Book.objects.get()
    assert book3.title == "The Tower of Fools"

    # When you have a relation, ormar always defines a related model for you
    # even when all you loaded is a foreign key value like in this example
    assert isinstance(book.author, Author)
    # primary key is populated from foreign key stored in books table
    assert book.author.pk == 1
    # since the related model was not loaded all other fields are None
    assert book.author.name is None

    # Load the relationship from the database when you already have the related model
    # alternatively see joins section below
    await book.author.load()
    assert book.author.name == "J.R.R. Tolkien"

    # get all rows for given model
    authors = await Author.objects.all()
    assert len(authors) == 2

    # to read more about reading data from the database
    # visit: https://collerek.github.io/ormar/queries/read/


async def update():
    # read existing row from db
    tolkien = await Author.objects.get(name="J.R.R. Tolkien")
    assert tolkien.name == "J.R.R. Tolkien"
    tolkien_id = tolkien.id

    # change the selected property
    tolkien.name = "John Ronald Reuel Tolkien"
    # call update on a model instance
    await tolkien.update()

    # confirm that object was updated
    tolkien = await Author.objects.get(name="John Ronald Reuel Tolkien")
    assert tolkien.name == "John Ronald Reuel Tolkien"
    assert tolkien.id == tolkien_id

    # alternatively update data without loading
    await Author.objects.filter(name__contains="Tolkien").update(name="J.R.R. Tolkien")

    # to read more about updating data in the database
    # visit: https://collerek.github.io/ormar/queries/update/


async def delete():
    silmarillion = await Book.objects.get(year=1977)
    # call delete() on instance
    await silmarillion.delete()

    # alternatively delete without loading
    await Book.objects.delete(title="The Tower of Fools")

    # note that when there is no record ormar raises NoMatch exception
    try:
        await Book.objects.get(year=1977)
    except ormar.NoMatch:
        print("No book from 1977!")

    # to read more about deleting data from the database
    # visit: https://collerek.github.io/ormar/queries/delete/

    # note that despite the fact that record no longer exists in database
    # the object above is still accessible and you can use it (and i.e. save()) again.
    tolkien = silmarillion.author
    await Book.objects.create(author=tolkien, title="The Silmarillion", year=1977)


async def joins():
    # Tho join two models use select_related

    # Django style
    book = await Book.objects.select_related("author").get(title="The Hobbit")
    # Python style
    book = await Book.objects.select_related(Book.author).get(
        Book.title == "The Hobbit"
    )

    # now the author is already prefetched
    assert book.author.name == "J.R.R. Tolkien"

    # By default you also get a second side of the relation
    # constructed as lowercase source model name +'s' (books in this case)
    # you can also provide custom name with parameter related_name
    # Django style
    author = await Author.objects.select_related("books").all(name="J.R.R. Tolkien")
    # Python style
    author = await Author.objects.select_related(Author.books).all(
        Author.name == "J.R.R. Tolkien"
    )
    assert len(author[0].books) == 3

    # for reverse and many to many relations you can also prefetch_related
    # that executes a separate query for each of related models

    # Django style
    author = await Author.objects.prefetch_related("books").get(name="J.R.R. Tolkien")
    # Python style
    author = await Author.objects.prefetch_related(Author.books).get(
        Author.name == "J.R.R. Tolkien"
    )
    assert len(author.books) == 3

    # to read more about relations
    # visit: https://collerek.github.io/ormar/relations/

    # to read more about joins and subqueries
    # visit: https://collerek.github.io/ormar/queries/joins-and-subqueries/


async def filter_and_sort():
    # to filter the query you can use filter() or pass key-value pars to
    # get(), all() etc.
    # to use special methods or access related model fields use double
    # underscore like to filter by the name of the author use author__name
    # Django style
    books = await Book.objects.all(author__name="J.R.R. Tolkien")
    # python style
    books = await Book.objects.all(Book.author.name == "J.R.R. Tolkien")
    assert len(books) == 3

    # filter can accept special methods also separated with double underscore
    # to issue sql query ` where authors.name like "%tolkien%"` that is not
    # case sensitive (hence small t in Tolkien)
    # Django style
    books = await Book.objects.filter(author__name__icontains="tolkien").all()
    # python style
    books = await Book.objects.filter(Book.author.name.icontains("tolkien")).all()
    assert len(books) == 3

    # to sort use order_by() function of queryset
    # to sort decreasing use hyphen before the field name
    # same as with filter you can use double underscores to access related fields
    # Django style
    books = (
        await Book.objects.filter(author__name__icontains="tolkien")
        .order_by("-year")
        .all()
    )
    # python style
    books = (
        await Book.objects.filter(Book.author.name.icontains("tolkien"))
        .order_by(Book.year.desc())
        .all()
    )
    assert len(books) == 3
    assert books[0].title == "The Silmarillion"
    assert books[2].title == "The Hobbit"

    # to read more about filtering and ordering
    # visit: https://collerek.github.io/ormar/queries/filter-and-sort/


async def subset_of_columns():
    # to exclude some columns from loading when querying the database
    # you can use fileds() method
    hobbit = await Book.objects.fields(["title"]).get(title="The Hobbit")
    # note that fields not included in fields are empty (set to None)
    assert hobbit.year is None
    assert hobbit.author is None

    # selected field is there
    assert hobbit.title == "The Hobbit"

    # alternatively you can provide columns you want to exclude
    hobbit = await Book.objects.exclude_fields(["year"]).get(title="The Hobbit")
    # year is still not set
    assert hobbit.year is None
    # but author is back
    assert hobbit.author is not None

    # also you cannot exclude primary key column - it's always there
    # even if you EXPLICITLY exclude it it will be there

    # note that each model have a shortcut for primary_key column which is pk
    # and you can filter/access/set the values by this alias like below
    assert hobbit.pk is not None

    # note that you cannot exclude fields that are not nullable
    # (required) in model definition
    try:
        await Book.objects.exclude_fields(["title"]).get(title="The Hobbit")
    except pydantic.ValidationError:
        print("Cannot exclude non nullable field title")

    # to read more about selecting subset of columns
    # visit: https://collerek.github.io/ormar/queries/select-columns/


async def pagination():
    # to limit number of returned rows use limit()
    books = await Book.objects.limit(1).all()
    assert len(books) == 1
    assert books[0].title == "The Hobbit"

    # to offset number of returned rows use offset()
    books = await Book.objects.limit(1).offset(1).all()
    assert len(books) == 1
    assert books[0].title == "The Lord of the Rings"

    # alternatively use paginate that combines both
    books = await Book.objects.paginate(page=2, page_size=2).all()
    assert len(books) == 2
    # note that we removed one book of Sapkowski in delete()
    # and recreated The Silmarillion - by default when no order_by is set
    # ordering sorts by primary_key column
    assert books[0].title == "The Witcher"
    assert books[1].title == "The Silmarillion"

    # to read more about pagination and number of rows
    # visit: https://collerek.github.io/ormar/queries/pagination-and-rows-number/


async def aggregations():
    # count:
    assert 2 == await Author.objects.count()

    # exists
    assert await Book.objects.filter(title="The Hobbit").exists()

    # maximum
    assert 1990 == await Book.objects.max(columns=["year"])

    # minimum
    assert 1937 == await Book.objects.min(columns=["year"])

    # average
    assert 1964.75 == await Book.objects.avg(columns=["year"])

    # sum
    assert 7859 == await Book.objects.sum(columns=["year"])

    # to read more about aggregated functions
    # visit: https://collerek.github.io/ormar/queries/aggregations/


async def raw_data():
    # extract raw data in a form of dicts or tuples
    # note that this skips the validation(!) as models are
    # not created from parsed data

    # get list of objects as dicts
    assert await Book.objects.values() == [
        {"id": 1, "author": 1, "title": "The Hobbit", "year": 1937},
        {"id": 2, "author": 1, "title": "The Lord of the Rings", "year": 1955},
        {"id": 4, "author": 2, "title": "The Witcher", "year": 1990},
        {"id": 5, "author": 1, "title": "The Silmarillion", "year": 1977},
    ]

    # get list of objects as tuples
    assert await Book.objects.values_list() == [
        (1, 1, "The Hobbit", 1937),
        (2, 1, "The Lord of the Rings", 1955),
        (4, 2, "The Witcher", 1990),
        (5, 1, "The Silmarillion", 1977),
    ]

    # filter data - note how you always get a list
    assert await Book.objects.filter(title="The Hobbit").values() == [
        {"id": 1, "author": 1, "title": "The Hobbit", "year": 1937}
    ]

    # select only wanted fields
    assert await Book.objects.filter(title="The Hobbit").values(["id", "title"]) == [
        {"id": 1, "title": "The Hobbit"}
    ]

    # if you select only one column you could flatten it with values_list
    assert await Book.objects.values_list("title", flatten=True) == [
        "The Hobbit",
        "The Lord of the Rings",
        "The Witcher",
        "The Silmarillion",
    ]

    # to read more about extracting raw values
    # visit: https://collerek.github.io/ormar/queries/aggregations/


async def with_connect(function):
    # note that for any other backend than sqlite you actually need to
    # connect to the database to perform db operations
    async with database:
        await function()

    # note that if you use framework like `fastapi` you shouldn't connect
    # in your endpoints but have a global connection pool
    # check https://collerek.github.io/ormar/fastapi/ and section with db connection


# gather and execute all functions
# note - normally import should be at the beginning of the file
import asyncio

# note that normally you use gather() function to run several functions
# concurrently but we actually modify the data and we rely on the order of functions
for func in [
    create,
    read,
    update,
    delete,
    joins,
    filter_and_sort,
    subset_of_columns,
    pagination,
    aggregations,
    raw_data,
]:
    print(f"Executing: {func.__name__}")
    asyncio.run(with_connect(func))

# drop the database tables
metadata.drop_all(engine)
