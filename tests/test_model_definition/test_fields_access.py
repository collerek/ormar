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


@pytest.mark.parametrize(
    "method, expected, expected_value",
    [
        ("__eq__", "exact", "Test"),
        ("__lt__", "lt", "Test"),
        ("__le__", "lte", "Test"),
        ("__ge__", "gte", "Test"),
        ("__gt__", "gt", "Test"),
        ("iexact", "iexact", "Test"),
        ("contains", "contains", "%Test%"),
        ("icontains", "icontains", "%Test%"),
        ("startswith", "startswith", "Test%"),
        ("istartswith", "istartswith", "Test%"),
        ("endswith", "endswith", "%Test"),
        ("iendswith", "iendswith", "%Test"),
        ("isnull", "isnull", "Test"),
        ("__contains__", "in", "Test"),
        ("__mod__", "contains", "%Test%"),
    ],
)
def test_operator_return_proper_filter_action(method, expected, expected_value):
    action = getattr(Product.name, method)("Test")
    assert action.source_model == Product
    assert action.target_model == Product
    assert action.operator == expected
    assert action.filter_value == expected_value

    action = getattr(Product.category.name, method)("Test")
    assert action.source_model == Product
    assert action.target_model == Category
    assert action.operator == expected
    assert action.filter_value == expected_value

    action = getattr(PriceList.categories.products.rating, method)("Test")
    assert action.source_model == PriceList
    assert action.target_model == Product
    assert action.operator == expected
    assert action.filter_value == expected_value


@pytest.mark.parametrize("method, expected_direction", [("asc", ""), ("desc", "desc"),])
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


# @pytest.mark.asyncio
# async def test_filtering_by_field_access():
#     async with database:
#         async with database.transaction(force_rollback=True):
#             category = await Category(name='Toys').save()
#             product1 = await Product(name="G.I Joe",
#                                      rating=4.7,
#                                      category=category).save()
#             product2 = await Product(name="My Little Pony",
#                                      rating=3.8,
#                                      category=category).save()
#
#             check = Product.object.get(Product.name == "My Little Pony")
#             assert check == product2

# TODO: Finish implementation
# * overload operators and add missing functions that return FilterAction (V)
# * return OrderAction for desc() and asc() (V)

# * accept args in all functions that accept filters? or only filter and exclude?
# all functions: delete, first, get, get_or_none, get_or_create, all, filter, exclude
# and same from queryset, should they also accept filter groups?
# * create filter groups for & and | (and ~ - NOT?)
# * accept OrderActions in order_by
#
