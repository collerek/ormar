from typing import List, Optional

import ormar
from ormar.models.excludable import ExcludableItems

from tests.settings import create_config
from tests.lifespan import init_tests

base_ormar_config = create_config()


class NickNames(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    is_lame: bool = ormar.Boolean(nullable=True)


class NicksHq(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="nicks_x_hq")


class HQ(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="hq_name")
    nicks: List[NickNames] = ormar.ManyToMany(NickNames, through=NicksHq)


class Company(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="companies")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100, nullable=False, name="company_name")
    founded: int = ormar.Integer(nullable=True)
    hq: HQ = ormar.ForeignKey(HQ)


class Car(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    manufacturer: Optional[Company] = ormar.ForeignKey(Company)
    name: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    gearbox_type: str = ormar.String(max_length=20, nullable=True)
    gears: int = ormar.Integer(nullable=True)
    aircon_type: str = ormar.String(max_length=20, nullable=True)


create_test_database = init_tests(base_ormar_config)


def compare_results(excludable):
    car_excludable = excludable.get(Car)
    assert car_excludable.exclude == {"year", "gearbox_type", "gears", "aircon_type"}
    assert car_excludable.include == set()

    assert car_excludable.is_excluded("year")

    alias = Company.ormar_config.alias_manager.resolve_relation_alias(
        Car, "manufacturer"
    )
    manu_excludable = excludable.get(Company, alias=alias)
    assert manu_excludable.exclude == {"founded"}
    assert manu_excludable.include == set()

    assert manu_excludable.is_excluded("founded")


def compare_results_include(excludable):
    manager = Company.ormar_config.alias_manager
    car_excludable = excludable.get(Car)
    assert car_excludable.include == {"id", "name"}
    assert car_excludable.exclude == set()

    assert car_excludable.is_included("name")
    assert not car_excludable.is_included("gears")

    alias = manager.resolve_relation_alias(Car, "manufacturer")
    manu_excludable = excludable.get(Company, alias=alias)
    assert manu_excludable.include == {"name"}
    assert manu_excludable.exclude == set()

    assert manu_excludable.is_included("name")
    assert not manu_excludable.is_included("founded")

    alias = manager.resolve_relation_alias(Company, "hq")
    hq_excludable = excludable.get(HQ, alias=alias)
    assert hq_excludable.include == {"name"}
    assert hq_excludable.exclude == set()

    alias = manager.resolve_relation_alias(NicksHq, "nicknames")
    nick_excludable = excludable.get(NickNames, alias=alias)
    assert nick_excludable.include == {"name"}
    assert nick_excludable.exclude == set()


def test_excluding_fields_from_list():
    fields = ["gearbox_type", "gears", "aircon_type", "year", "manufacturer__founded"]
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=True)
    compare_results(excludable)


def test_excluding_fields_from_dict():
    fields = {
        "gearbox_type": ...,
        "gears": ...,
        "aircon_type": ...,
        "year": ...,
        "manufacturer": {"founded": ...},
    }
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=True)
    compare_results(excludable)


def test_excluding_fields_from_dict_with_set():
    fields = {
        "gearbox_type": ...,
        "gears": ...,
        "aircon_type": ...,
        "year": ...,
        "manufacturer": {"founded"},
    }
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=True)
    compare_results(excludable)


def test_gradual_build_from_lists():
    fields_col = [
        "year",
        ["gearbox_type", "gears"],
        "aircon_type",
        ["manufacturer__founded"],
    ]
    excludable = ExcludableItems()
    for fields in fields_col:
        excludable.build(items=fields, model_cls=Car, is_exclude=True)
    compare_results(excludable)


def test_nested_includes():
    fields = [
        "id",
        "name",
        "manufacturer__name",
        "manufacturer__hq__name",
        "manufacturer__hq__nicks__name",
    ]
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=False)
    compare_results_include(excludable)


def test_nested_includes_from_dict():
    fields = {
        "id": ...,
        "name": ...,
        "manufacturer": {"name": ..., "hq": {"name": ..., "nicks": {"name": ...}}},
    }
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=False)
    compare_results_include(excludable)


def test_nested_includes_from_dict_with_set():
    fields = {
        "id": ...,
        "name": ...,
        "manufacturer": {"name": ..., "hq": {"name": ..., "nicks": {"name"}}},
    }
    excludable = ExcludableItems()
    excludable.build(items=fields, model_cls=Car, is_exclude=False)
    compare_results_include(excludable)


def test_includes_and_excludes_combo():
    fields_inc1 = ["id", "name", "year", "gearbox_type", "gears"]
    fields_inc2 = {"manufacturer": {"name"}}
    fields_exc1 = {"manufacturer__founded"}
    fields_exc2 = "aircon_type"
    excludable = ExcludableItems()
    excludable.build(items=fields_inc1, model_cls=Car, is_exclude=False)
    excludable.build(items=fields_inc2, model_cls=Car, is_exclude=False)
    excludable.build(items=fields_exc1, model_cls=Car, is_exclude=True)
    excludable.build(items=fields_exc2, model_cls=Car, is_exclude=True)

    car_excludable = excludable.get(Car)
    assert car_excludable.include == {"id", "name", "year", "gearbox_type", "gears"}
    assert car_excludable.exclude == {"aircon_type"}

    assert car_excludable.is_excluded("aircon_type")
    assert car_excludable.is_included("name")

    alias = Company.ormar_config.alias_manager.resolve_relation_alias(
        Car, "manufacturer"
    )
    manu_excludable = excludable.get(Company, alias=alias)
    assert manu_excludable.include == {"name"}
    assert manu_excludable.exclude == {"founded"}

    assert manu_excludable.is_excluded("founded")
