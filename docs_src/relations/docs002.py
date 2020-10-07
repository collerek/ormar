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

    # If there are no additional columns id will be created automatically as Integer


class Post(ormar.Model):
    class Meta:
        tablename = "posts"
        database = database
        metadata = metadata

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    categories: ormar.ManyToMany(Category, through=PostCategory)
    author: ormar.ForeignKey(Author)
