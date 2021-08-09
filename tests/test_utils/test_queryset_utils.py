import databases
import sqlalchemy

import ormar
from ormar.queryset.prefetch_query import sort_models
from ormar.queryset.utils import (
    subtract_dict,
    translate_list_to_dict,
    update,
    update_dict_from_list,
)
from tests.settings import DATABASE_URL


def test_list_to_dict_translation():
    tet_list = ["aa", "bb", "cc__aa", "cc__bb", "cc__aa__xx", "cc__aa__yy"]
    test = translate_list_to_dict(tet_list)
    assert test == {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx": Ellipsis, "yy": Ellipsis}, "bb": Ellipsis},
    }


def test_updating_dict_with_list():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx": Ellipsis, "yy": Ellipsis}, "bb": Ellipsis},
    }
    list_to_update = ["ee", "bb__cc", "cc__aa__xx__oo", "cc__aa__oo"]
    test = update_dict_from_list(curr_dict, list_to_update)
    assert test == {
        "aa": Ellipsis,
        "bb": {"cc": Ellipsis},
        "cc": {
            "aa": {"xx": {"oo": Ellipsis}, "yy": Ellipsis, "oo": Ellipsis},
            "bb": Ellipsis,
        },
        "ee": Ellipsis,
    }


def test_updating_dict_inc_set_with_list():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx", "yy"}, "bb": Ellipsis},
    }
    list_to_update = ["uu", "bb__cc", "cc__aa__xx__oo", "cc__aa__oo"]
    test = update_dict_from_list(curr_dict, list_to_update)
    assert test == {
        "aa": Ellipsis,
        "bb": {"cc": Ellipsis},
        "cc": {
            "aa": {"xx": {"oo": Ellipsis}, "yy": Ellipsis, "oo": Ellipsis},
            "bb": Ellipsis,
        },
        "uu": Ellipsis,
    }


def test_updating_dict_inc_set_with_dict():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx", "yy"}, "bb": Ellipsis},
    }
    dict_to_update = {
        "uu": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {"aa": {"xx": {"oo": Ellipsis}, "oo": Ellipsis}},
    }
    test = update(curr_dict, dict_to_update)
    assert test == {
        "aa": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {
            "aa": {"xx": {"oo": Ellipsis}, "yy": Ellipsis, "oo": Ellipsis},
            "bb": Ellipsis,
        },
        "uu": Ellipsis,
    }


def test_subtracting_dict_inc_set_with_dict():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx", "yy"}, "bb": Ellipsis},
    }
    dict_to_update = {
        "uu": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {"aa": {"xx": {"oo": Ellipsis}}, "bb": Ellipsis},
    }
    test = subtract_dict(curr_dict, dict_to_update)
    assert test == {"aa": Ellipsis, "cc": {"aa": {"yy": Ellipsis}}}


def test_updating_dict_inc_set_with_dict_inc_set():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx", "yy"}, "bb": Ellipsis},
    }
    dict_to_update = {
        "uu": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {"aa": {"xx", "oo", "zz", "ii"}},
    }
    test = update(curr_dict, dict_to_update)
    assert test == {
        "aa": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {"aa": {"xx", "yy", "oo", "zz", "ii"}, "bb": Ellipsis},
        "uu": Ellipsis,
    }


def test_subtracting_dict_inc_set_with_dict_inc_set():
    curr_dict = {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx", "yy"}, "bb": Ellipsis},
        "dd": {"aa", "bb"},
    }
    dict_to_update = {
        "aa": Ellipsis,
        "bb": {"cc", "dd"},
        "cc": {"aa": {"xx", "oo", "zz", "ii"}},
        "dd": {"aa", "bb"},
    }
    test = subtract_dict(curr_dict, dict_to_update)
    assert test == {"cc": {"aa": {"yy"}, "bb": Ellipsis}}


def test_subtracting_with_set_and_dict():
    curr_dict = {
        "translation": {
            "filters": {
                "values": Ellipsis,
                "reports": {"report": {"charts": {"chart": Ellipsis}}},
            },
            "translations": {"language": Ellipsis},
            "filtervalues": {
                "filter": {"reports": {"report": {"charts": {"chart": Ellipsis}}}}
            },
        },
        "chart": {
            "reports": {
                "report": {
                    "filters": {
                        "filter": {
                            "translation": {
                                "translations": {"language": Ellipsis},
                                "filtervalues": Ellipsis,
                            },
                            "values": {
                                "translation": {"translations": {"language": Ellipsis}}
                            },
                        }
                    }
                }
            }
        },
    }
    dict_to_update = {
        "chart": Ellipsis,
        "translation": {"filters", "filtervalues", "chartcolumns"},
    }
    test = subtract_dict(curr_dict, dict_to_update)
    assert test == {"translation": {"translations": {"language": Ellipsis}}}


database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class SortModel(ormar.Model):
    class Meta:
        tablename = "sorts"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    sort_order: int = ormar.Integer()


def test_sorting_models():
    models = [
        SortModel(id=1, name="Alice", sort_order=0),
        SortModel(id=2, name="Al", sort_order=1),
        SortModel(id=3, name="Zake", sort_order=1),
        SortModel(id=4, name="Will", sort_order=0),
        SortModel(id=5, name="Al", sort_order=2),
        SortModel(id=6, name="Alice", sort_order=2),
    ]
    orders_by = {"name": "asc", "none": {}, "sort_order": "desc"}
    models = sort_models(models, orders_by)
    assert models[5].name == "Zake"
    assert models[0].name == "Al"
    assert models[1].name == "Al"
    assert [model.id for model in models] == [5, 2, 6, 1, 4, 3]

    orders_by = {"name": "asc", "none": set("aa"), "id": "asc"}
    models = sort_models(models, orders_by)
    assert [model.id for model in models] == [2, 5, 1, 6, 4, 3]

    orders_by = {"sort_order": "asc", "none": ..., "id": "asc", "uu": 2, "aa": None}
    models = sort_models(models, orders_by)
    assert [model.id for model in models] == [1, 4, 2, 3, 5, 6]
