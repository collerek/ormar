# Transactions

Database transactions are supported through ormar's `DatabaseConnection` class, which internally uses SQLAlchemy async to manage transactions with context variables and savepoints.

## Basic usage

To use transactions use `database.transaction()` as async context manager:

```python
async with database.transaction():
    # everything called here will be one transaction
    await Model1().save()
    await Model2().save()
    # if any exception occurs, all changes will be rolled back
    # if successful, changes will be committed automatically
```

!!!note
    Note that it has to be the same `database` that the one used in Model's `ormar_config` object.

To avoid passing `database` instance around in your code you can extract the instance from each `Model`.
Database provided during declaration of `ormar.Model` is available through `ormar_config.database` and can
be reached from both class and instance.

```python
import sqlalchemy
import ormar
from ormar import DatabaseConnection


base_ormar_config = ormar.OrmarConfig(
    metadata=sqlalchemy.MetaData(),
    database=DatabaseConnection("sqlite+aiosqlite:///db.sqlite"),
)


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=255)
    author: Author = ormar.ForeignKey(Author)


# database is accessible from class
database = Author.ormar_config.database

# as well as from instance
author = Author(name="Stephen King")
database = author.ormar_config.database

# Example: Using transaction to ensure atomicity
async def create_author_with_book():
    async with database:
        async with database.transaction():
            author = await Author.objects.create(name="Stephen King")
            book = await Book.objects.create(
                title="The Shining",
                author=author
            )
            # Both author and book are created in one transaction
            # If book creation fails, author creation is rolled back
```

## Nested Transactions

Transaction blocks are managed as task-local state using context variables. Nested transactions
are fully supported and are implemented using SQLAlchemy savepoints.

```python
async def create_multiple_authors_with_books():
    async with database:
        # Outer transaction
        async with database.transaction():
            author1 = await Author.objects.create(name="Stephen King")

            # Nested transaction (uses savepoint)
            try:
                async with database.transaction():
                    book1 = await Book.objects.create(
                        title="The Shining",
                        author=author1
                    )
                    # Simulate an error
                    raise ValueError("Something went wrong!")
            except ValueError:
                # Inner transaction is rolled back to savepoint
                # author1 is still in the outer transaction
                pass

            # Continue with outer transaction
            author2 = await Author.objects.create(name="J.K. Rowling")
            book2 = await Book.objects.create(
                title="Harry Potter",
                author=author2
            )
            # author1, author2, and book2 are committed
            # book1 was rolled back
```

## Force Rollback for Testing

Transactions can be extremely useful during testing when you can apply force rollback
and you do not have to clean the data after each test. The `force_rollback=True` parameter
will rollback the transaction even if it completes successfully.

```python
import pytest

@pytest.mark.asyncio
async def test_author_creation():
    async with database:
        async with database.transaction(force_rollback=True):
            # Create test data
            author = await Author.objects.create(name="Test Author")
            book = await Book.objects.create(
                title="Test Book",
                author=author
            )

            # Verify the data was created
            assert await Author.objects.count() == 1
            assert await Book.objects.count() == 1

            # After the transaction exits, everything is rolled back
            # No cleanup needed!

        # Verify data was rolled back
        assert await Author.objects.count() == 0
        assert await Book.objects.count() == 0
```

## Complete Example with Error Handling

Here's a comprehensive example showing transaction usage with error handling:

```python
import sqlalchemy
import ormar
from ormar import DatabaseConnection


DATABASE_URL = "sqlite+aiosqlite:///db.sqlite"

base_ormar_config = ormar.OrmarConfig(
    metadata=sqlalchemy.MetaData(),
    database=DatabaseConnection(DATABASE_URL),
)


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=255)
    author: Author = ormar.ForeignKey(Author)


async def create_author_and_books_transactional(author_name: str, book_titles: list[str]):
    """
    Create an author and multiple books in a single transaction.
    If any book fails to create, the entire operation is rolled back.
    """
    database = Author.ormar_config.database

    async with database:
        try:
            async with database.transaction():
                # Create author
                author = await Author.objects.create(name=author_name)

                # Create all books
                for title in book_titles:
                    await Book.objects.create(title=title, author=author)

                print(f"Successfully created {author_name} with {len(book_titles)} books")
                return author

        except Exception as e:
            # Transaction is automatically rolled back on exception
            print(f"Failed to create author and books: {e}")
            # Author and all books are rolled back
            raise


# Usage example
async def main():
    database = Author.ormar_config.database

    async with database:
        # Create tables
        sync_engine = sqlalchemy.create_engine(
            DATABASE_URL.replace('+aiosqlite', '')
        )
        base_ormar_config.metadata.create_all(sync_engine)

        # Example 1: Successful transaction
        await create_author_and_books_transactional(
            "Stephen King",
            ["The Shining", "It", "The Stand"]
        )

        # Example 2: Failed transaction (will rollback)
        try:
            await create_author_and_books_transactional(
                "Test Author",
                ["Book 1", None, "Book 3"]  # None will cause an error
            )
        except Exception:
            print("Transaction rolled back as expected")

        # Verify: Only Stephen King and his books exist
        authors = await Author.objects.all()
        print(f"Total authors: {len(authors)}")  # Should be 1

        books = await Book.objects.all()
        print(f"Total books: {len(books)}")  # Should be 3


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Transaction Context Management

Ormar manages transactions using context variables, which means:

1. **Thread-safe**: Each async task has its own transaction context
2. **Automatic connection reuse**: Within a transaction, all queries use the same database connection
3. **Savepoint support**: Nested transactions create savepoints automatically
4. **Rollback on exception**: If an exception occurs, the transaction is automatically rolled back
5. **Automatic commit**: If the transaction block completes successfully, changes are committed

## Best Practices

1. **Keep transactions short**: Long-running transactions can cause lock contention
2. **Don't mix transaction and non-transaction operations**: Once in a transaction, all operations should be part of it
3. **Use force_rollback for tests**: Avoid test data pollution by rolling back test transactions
4. **Handle exceptions appropriately**: Let exceptions propagate to trigger rollback, or catch and handle them within the transaction
5. **Use nested transactions for partial rollbacks**: When you need fine-grained control over what gets rolled back
