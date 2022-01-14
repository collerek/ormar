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

await Book.objects.update(each=True, genre='Fiction')
all_books = await Book.objects.filter(genre='Fiction').all()
assert len(all_books) == 3
