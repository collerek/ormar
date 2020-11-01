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
await Book.objects.create(title='War and Peace in Space', author="Tolstoy, Leo", genre='Fantasy')
await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')

# delete accepts kwargs that will be used in filter
# acting in same way as queryset.filter(**kwargs).delete()
await Book.objects.delete(genre='Fantasy')  # delete all fantasy books
all_books = await Book.objects.all()
assert len(all_books) == 2
