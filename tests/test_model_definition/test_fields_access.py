import pytest

import ormar
from ormar import BaseField
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class PriceList(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="price_lists")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    price_lists = ormar.ManyToMany(PriceList, related_name="categories")


class Product(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="product")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    rating: float = ormar.Float(minimum=1, maximum=5)
    category = ormar.ForeignKey(Category)


class Supplier(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="suppliers")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="items")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    supplier = ormar.ForeignKey(Supplier, name="supplier_id")


create_test_database = init_tests(base_ormar_config)


def test_fields_access():
    # basic access
    assert Product.id._field == Product.ormar_config.model_fields["id"]
    assert Product.id.id == Product.ormar_config.model_fields["id"]
    assert Product.pk.id == Product.id.id
    assert isinstance(Product.id._field, BaseField)
    assert Product.id._access_chain == "id"
    assert Product.id._source_model == Product

    # nested models
    curr_field = Product.category.name
    assert curr_field._field == Category.ormar_config.model_fields["name"]
    assert curr_field._access_chain == "category__name"
    assert curr_field._source_model == Product

    # deeper nesting
    curr_field = Product.category.price_lists.name
    assert curr_field._field == PriceList.ormar_config.model_fields["name"]
    assert curr_field._access_chain == "category__price_lists__name"
    assert curr_field._source_model == Product

    # reverse nesting
    curr_field = PriceList.categories.products.rating
    assert curr_field._field == Product.ormar_config.model_fields["rating"]
    assert curr_field._access_chain == "categories__products__rating"
    assert curr_field._source_model == PriceList

    # FK accessor accepts the same operators as a regular field
    sample_category = Category(id=7, name="x")
    assert (Product.category == 3)._kwargs_dict == {"category__exact": 3}
    assert (Product.category == sample_category)._kwargs_dict == {
        "category__exact": sample_category
    }
    assert (Product.category >= 3)._kwargs_dict == {"category__gte": 3}
    assert (Product.category <= 3)._kwargs_dict == {"category__lte": 3}
    assert (Product.category > 3)._kwargs_dict == {"category__gt": 3}
    assert (Product.category < 3)._kwargs_dict == {"category__lt": 3}
    assert (Product.category << [1, 2])._kwargs_dict == {"category__in": [1, 2]}
    assert Product.category.in_([1, 2])._kwargs_dict == {"category__in": [1, 2]}
    assert (Product.category >> None)._kwargs_dict == {"category__isnull": True}
    assert Product.category.isnull(False)._kwargs_dict == {"category__isnull": False}

    # FK accessor with an explicit db alias (name="supplier_id") still works
    # because the check keys on the ormar field registry, not on table.columns
    sample_supplier = Supplier(id=9, name="acme")
    assert (Item.supplier == 2)._kwargs_dict == {"supplier__exact": 2}
    assert (Item.supplier == sample_supplier)._kwargs_dict == {
        "supplier__exact": sample_supplier
    }
    assert (Item.supplier << [sample_supplier, 5])._kwargs_dict == {
        "supplier__in": [sample_supplier, 5]
    }
    assert (Item.supplier >= 2)._kwargs_dict == {"supplier__gte": 2}

    # m2m accessor has no own column - comparison still raises
    with pytest.raises(AttributeError):
        assert Category.price_lists >= 3

    # reverse FK accessor (virtual relation) - comparison still raises
    with pytest.raises(AttributeError):
        assert Category.products >= 3


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
    ) == ("NOT ((product.name = 'Test') AND (product.rating >= 3.0))")

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
        f"OR ({price_list_prefix}_price_lists.name LIKE 'Aa%') "
        f"OR ({category_prefix}_categories.name IN ('Toys', 'Books')))"
    )

    group = (Product.name % "Test") & (
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
        f"AND (({price_list_prefix}_price_lists.name LIKE 'Aa%') "
        f"OR ({category_prefix}_categories.name IN ('Toys', 'Books'))))"
    )


@pytest.mark.asyncio
async def test_filtering_by_field_access():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            category = await Category(name="Toys").save()
            product2 = await Product(
                name="My Little Pony", rating=3.8, category=category
            ).save()

            check = await Product.objects.get(Product.name == "My Little Pony")
            assert check == product2


@pytest.mark.asyncio
async def test_filtering_fk_by_field_access():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            toys = await Category(name="Toys").save()
            books = await Category(name="Books").save()
            pony = await Product(
                name="My Little Pony", rating=3.8, category=toys
            ).save()
            await Product(name="Novel", rating=4.2, category=books).save()

            # by scalar PK - should match kwargs form exactly
            via_accessor = await Product.objects.filter(
                Product.category == toys.pk
            ).all()
            via_kwargs = await Product.objects.filter(category=toys.pk).all()
            assert {p.pk for p in via_accessor} == {pony.pk}
            assert {p.pk for p in via_accessor} == {p.pk for p in via_kwargs}

            # by model instance
            via_instance = await Product.objects.filter(Product.category == toys).all()
            assert {p.pk for p in via_instance} == {pony.pk}

            # `in_` / `<<` returns matches for several PKs
            all_products = await Product.objects.all()
            via_in = await Product.objects.filter(
                Product.category << [toys.pk, books.pk]
            ).all()
            assert {p.pk for p in via_in} == {p.pk for p in all_products}

            # aliased FK field (name="supplier_id")
            sup = await Supplier(name="Acme").save()
            other_sup = await Supplier(name="Globex").save()
            gadget = await Item(name="gadget", supplier=sup).save()
            await Item(name="widget", supplier=other_sup).save()
            via_aliased_pk = await Item.objects.filter(Item.supplier == sup.pk).all()
            via_aliased_instance = await Item.objects.filter(Item.supplier == sup).all()
            via_aliased_in = await Item.objects.filter(
                Item.supplier << [sup.pk, other_sup.pk]
            ).all()
            assert {i.pk for i in via_aliased_pk} == {gadget.pk}
            assert {i.pk for i in via_aliased_instance} == {gadget.pk}
            assert len(via_aliased_in) == 2
