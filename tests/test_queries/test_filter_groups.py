from typing import Optional

import ormar

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: Optional[int] = ormar.Integer(nullable=True)


create_test_database = init_tests(base_ormar_config)


def test_or_group():
    result = ormar.or_(name="aa", books__title="bb")
    result.resolve(model_cls=Author)
    assert len(result.actions) == 2
    assert result.actions[0].target_model == Author
    assert result.actions[1].target_model == Book
    assert (
        str(result.get_text_clause().compile(compile_kwargs={"literal_binds": True}))
        == f"(authors.name = 'aa' OR "
        f"{result.actions[1].table_prefix}"
        f"_books.title = 'bb')"
    )


def test_and_group():
    result = ormar.and_(name="aa", books__title="bb")
    result.resolve(model_cls=Author)
    assert len(result.actions) == 2
    assert result.actions[0].target_model == Author
    assert result.actions[1].target_model == Book
    assert (
        str(result.get_text_clause().compile(compile_kwargs={"literal_binds": True}))
        == f"(authors.name = 'aa' AND "
        f"{result.actions[1].table_prefix}"
        f"_books.title = 'bb')"
    )


def test_nested_and():
    result = ormar.and_(
        ormar.or_(name="aa", books__title="bb"), ormar.or_(name="cc", books__title="dd")
    )
    result.resolve(model_cls=Author)
    assert len(result.actions) == 0
    assert len(result._nested_groups) == 2
    book_prefix = result._nested_groups[0].actions[1].table_prefix
    assert (
        str(result.get_text_clause().compile(compile_kwargs={"literal_binds": True}))
        == f"((authors.name = 'aa' OR "
        f"{book_prefix}"
        f"_books.title = 'bb') AND "
        f"(authors.name = 'cc' OR "
        f"{book_prefix}"
        f"_books.title = 'dd'))"
    )


def test_nested_group_and_action():
    result = ormar.and_(ormar.or_(name="aa", books__title="bb"), books__title="dd")
    result.resolve(model_cls=Author)
    assert len(result.actions) == 1
    assert len(result._nested_groups) == 1
    book_prefix = result._nested_groups[0].actions[1].table_prefix
    assert (
        str(result.get_text_clause().compile(compile_kwargs={"literal_binds": True}))
        == f"((authors.name = 'aa' OR "
        f"{book_prefix}"
        f"_books.title = 'bb') AND "
        f"{book_prefix}"
        f"_books.title = 'dd')"
    )


def test_deeply_nested_or():
    result = ormar.or_(
        ormar.and_(
            ormar.or_(name="aa", books__title="bb"),
            ormar.or_(name="cc", books__title="dd"),
        ),
        ormar.and_(
            ormar.or_(books__year__lt=1900, books__title="11"),
            ormar.or_(books__year__gt="xx", books__title="22"),
        ),
    )
    result.resolve(model_cls=Author)
    assert len(result.actions) == 0
    assert len(result._nested_groups) == 2
    assert len(result._nested_groups[0]._nested_groups) == 2
    book_prefix = result._nested_groups[0]._nested_groups[0].actions[1].table_prefix
    result_qry = str(
        result.get_text_clause().compile(compile_kwargs={"literal_binds": True})
    )
    expected_qry = (
        f"(((authors.name = 'aa' OR {book_prefix}_books.title = 'bb') AND "
        f"(authors.name = 'cc' OR {book_prefix}_books.title = 'dd')) "
        f"OR (({book_prefix}_books.year < 1900 OR {book_prefix}_books.title = '11') AND"
        f" ({book_prefix}_books.year > 'xx' OR {book_prefix}_books.title = '22')))"
    )
    assert result_qry.replace("\n", "") == expected_qry.replace("\n", "")


def test_one_model_group():
    result = ormar.and_(year__gt=1900, title="bb")
    result.resolve(model_cls=Book)
    assert len(result.actions) == 2
    assert len(result._nested_groups) == 0


def test_one_model_nested_group():
    result = ormar.and_(
        ormar.or_(year__gt=1900, title="bb"), ormar.or_(year__lt=1800, title="aa")
    )
    result.resolve(model_cls=Book)
    assert len(result.actions) == 0
    assert len(result._nested_groups) == 2


def test_one_model_with_group():
    result = ormar.or_(ormar.and_(year__gt=1900, title="bb"), title="uu")
    result.resolve(model_cls=Book)
    assert len(result.actions) == 1
    assert len(result._nested_groups) == 1
