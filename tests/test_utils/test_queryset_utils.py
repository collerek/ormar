from ormar.queryset.utils import (
    subtract_dict,
    translate_list_to_dict,
    update,
    update_dict_from_list,
)

from tests.settings import create_config

base_ormar_config = create_config()


def test_list_to_dict_translation():
    tet_list = ["aa", "bb", "cc__aa", "cc__bb", "cc__aa__xx", "cc__aa__yy"]
    test = translate_list_to_dict(tet_list)
    assert test == {
        "aa": Ellipsis,
        "bb": Ellipsis,
        "cc": {"aa": {"xx": Ellipsis, "yy": Ellipsis}, "bb": Ellipsis},
    }


def test_list_to_dict_translation_with_default():
    tet_list = ["aa", "aa__inner", "bb"]
    testshallow = translate_list_to_dict(tet_list, default={})
    assert testshallow == {"aa": {"inner": {}}, "bb": {}}

    tet_list = ["aa", "aa__inner", "bb"]
    testdeep = translate_list_to_dict(tet_list, default={"foo": {}})
    assert testdeep == {"aa": {"foo": {}, "inner": {"foo": {}}}, "bb": {"foo": {}}}
    testdeep["aa"]["foo"]["bar"] = 1234
    assert testdeep == {
        "aa": {"foo": {"bar": 1234}, "inner": {"foo": {}}},
        "bb": {"foo": {}},
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
