from typing import Dict, Set, Union


class Excludable:
    @staticmethod
    def get_child(
        items: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        if isinstance(items, dict):
            return items.get(key, {})
        return items

    @staticmethod
    def get_excluded(
        exclude: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        return Excludable.get_child(items=exclude, key=key)

    @staticmethod
    def get_included(
        include: Union[Set, Dict, None], key: str = None
    ) -> Union[Set, Dict, None]:
        return Excludable.get_child(items=include, key=key)

    @staticmethod
    def is_excluded(exclude: Union[Set, Dict, None], key: str = None) -> bool:
        if exclude is None:
            return False
        if exclude is Ellipsis:  # pragma: nocover
            return True
        to_exclude = Excludable.get_excluded(exclude=exclude, key=key)
        if isinstance(to_exclude, Set):
            return key in to_exclude
        if to_exclude is ...:
            return True
        return False

    @staticmethod
    def is_included(include: Union[Set, Dict, None], key: str = None) -> bool:
        if include is None:
            return True
        if include is Ellipsis:
            return True
        to_include = Excludable.get_included(include=include, key=key)
        if isinstance(to_include, Set):
            return key in to_include
        if to_include is ...:
            return True
        return False
