import json

from ormar.queryset.utils import to_str


def test_to_str():
    expected_str = "[]"
    val = json.dumps([])
    assert expected_str == to_str(val)

    expected_bytes = expected_str.encode()
    assert isinstance(expected_bytes, bytes)

    assert isinstance(to_str(expected_bytes), str)
    assert "1" == to_str(1)
