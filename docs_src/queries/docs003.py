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

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: str = ormar.String(max_length=100)
    genre: str = ormar.String(max_length=100, default='Fiction',
                              choices=['Fiction', 'Adventure', 'Historic', 'Fantasy'])


await Book.objects.create(title='Tom Sawyer', author="Twain, Mark", genre='Adventure')
await Book.objects.create(title='War and Peace', author="Tolstoy, Leo", genre='Fiction')
await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')

# if not exist the instance will be persisted in db
vol2 = await Book.objects.update_or_create(title="Volume II", author='Anonymous', genre='Fiction')
assert await Book.objects.count() == 1

# if pk or pkname passed in kwargs (like id here) the object will be updated
assert await Book.objects.update_or_create(id=vol2.id, genre='Historic')
assert await Book.objects.count() == 1
