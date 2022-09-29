import databases
import pytest
import sqlalchemy

import ormar
from ormar import BaseField
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class PriceList(ormar.Model):
    class Meta(BaseMeta):
        tablename = "price_lists"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    price_lists = ormar.ManyToMany(PriceList, related_name="categories")


class Product(ormar.Model):
    class Meta(BaseMeta):
        tablename = "product"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    rating: float = ormar.Float(minimum=1, maximum=5)
    category = ormar.ForeignKey(Category)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_fields_access():
    # basic access
    assert Product.id._field == Product.Meta.model_fields["id"]
    assert Product.id.id == Product.Meta.model_fields["id"]
    assert Product.pk.id == Product.id.id
    assert isinstance(Product.id._field, BaseField)
    assert Product.id._access_chain == "id"
    assert Product.id._source_model == Product

    # nested models
    curr_field = Product.category.name
    assert curr_field._field == Category.Meta.model_fields["name"]
    assert curr_field._access_chain == "category__name"
    assert curr_field._source_model == Product

    # deeper nesting
    curr_field = Product.category.price_lists.name
    assert curr_field._field == PriceList.Meta.model_fields["name"]
    assert curr_field._access_chain == "category__price_lists__name"
    assert curr_field._source_model == Product

    # reverse nesting
    curr_field = PriceList.categories.products.rating
    assert curr_field._field == Product.Meta.model_fields["rating"]
    assert curr_field._access_chain == "categories__products__rating"
    assert curr_field._source_model == PriceList

    with pytest.raises(AttributeError):
        assert Category.price_lists >= 3


@pytest.mark.parametrize(
    "method, expected, expected_value",
    [
        ("__eq__", "exact", "Test"),
        ("__lt__", "lt", "Test"),
        ("__le__", "lte", "Test"),
        ("__ge__", "gte", "Test"),
        ("__gt__", "gt", "Test"),
        ("iexact", "iexact", "Test"),
        ("contains", "contains", "Test"),
        ("icontains", "icontains", "Test"),
        ("startswith", "startswith", "Test"),
        ("istartswith", "istartswith", "Test"),
        ("endswith", "endswith", "Test"),
        ("iendswith", "iendswith", "Test"),
        ("isnull", "isnull", "Test"),
        ("in_", "in", "Test"),
        ("__lshift__", "in", "Test"),
        ("__rshift__", "isnull", True),
        ("__mod__", "contains", "Test"),
    ],
)
def test_operator_return_proper_filter_action(method, expected, expected_value):
    group_ = getattr(Product.name, method)("Test")
    assert group_._kwargs_dict == {f"name__{expected}": expected_value}

    group_ = getattr(Product.category.name, method)("Test")
    assert group_._kwargs_dict == {f"category__name__{expected}": expected_value}

    group_ = getattr(PriceList.categories.products.rating, method)("Test")
    assert group_._kwargs_dict == {
        f"categories__products__rating__{expected}": expected_value
    }


@pytest.mark.parametrize("method, expected_direction", [("asc", ""), ("desc", "desc")])
def test_operator_return_proper_order_action(method, expected_direction):
    action = getattr(Product.name, method)()
    assert action.source_model == Product
    assert action.target_model == Product
    assert action.direction == expected_direction
    assert action.is_source_model_order

    action = getattr(Product.category.name, method)()
    assert action.source_model == Product
    assert action.target_model == Category
    assert action.direction == expected_direction
    assert not action.is_source_model_order

    action = getattr(PriceList.categories.products.rating, method)()
    assert action.source_model == PriceList
    assert action.target_model == Product
    assert action.direction == expected_direction
    assert not action.is_source_model_order


def test_combining_groups_together():
    group = (Product.name == "Test") & (Product.rating >= 3.0)
    group.resolve(model_cls=Product)
    assert len(group._nested_groups) == 2
    assert str(
        group.get_text_clause().compile(compile_kwargs={"literal_binds": True})
    ) == ("((product.name = 'Test') AND (product.rating >= 3.0))")

    group = ~((Product.name == "Test") & (Product.rating >= 3.0))
    group.resolve(model_cls=Product)
    assert len(group._nested_groups) == 2
    assert str(
        group.get_text_clause().compile(compile_kwargs={"literal_binds": True})
    ) == ("NOT ((product.name = 'Test') AND" " (product.rating >= 3.0))")

    group = ((Product.name == "Test") & (Product.rating >= 3.0)) | (
        Product.category.name << (["Toys", "Books"])
    )
    group.resolve(model_cls=Product)
    assert len(group._nested_groups) == 2
    assert len(group._nested_groups[0]._nested_groups) == 2
    group_str = str(
        group.get_text_clause().compile(compile_kwargs={"literal_binds": True})
    )
    category_prefix = group._nested_groups[1].actions[0].table_prefix
    assert group_str == (
        "(((product.name = 'Test') AND (product.rating >= 3.0)) "
        f"OR ({category_prefix}_categories.name IN ('Toys', 'Books')))"
    )

    group = (Product.name % "Test") | (
        (Product.category.price_lists.name.startswith("Aa"))
        | (Product.category.name << (["Toys", "Books"]))
    )
    group.resolve(model_cls=Product)
    assert len(group._nested_groups) == 2
    assert len(group._nested_groups[1]._nested_groups) == 2
    group_str = str(
        group.get_text_clause().compile(compile_kwargs={"literal_binds": True})
    )
    price_list_prefix = (
        group._nested_groups[1]._nested_groups[0].actions[0].table_prefix
    )
    category_prefix = group._nested_groups[1]._nested_groups[1].actions[0].table_prefix
    assert group_str == (
        f"((product.name LIKE '%Test%') "
        f"OR (({price_list_prefix}_price_lists.name LIKE 'Aa%') "
        f"OR ({category_prefix}_categories.name IN ('Toys', 'Books'))))"
    )


@pytest.mark.asyncio
async def test_filtering_by_field_access():
    async with database:
        async with database.transaction(force_rollback=True):
            category = await Category(name="Toys").save()
            product2 = await Product(
                name="My Little Pony", rating=3.8, category=category
            ).save()

            check = await Product.objects.get(Product.name == "My Little Pony")
            assert check == product2
