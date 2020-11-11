from ormar.models.excludable import Excludable
from ormar.queryset.utils import translate_list_to_dict, update_dict_from_list, update


def test_empty_excludable():
    assert Excludable.is_included(None, "key")  # all fields included if empty
    assert not Excludable.is_excluded(None, "key")  # none field excluded if empty


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
