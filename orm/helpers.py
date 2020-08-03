from typing import Union, Set, Dict  # pragma no cover


class Excludable:  # pragma no cover

    @staticmethod
    def get_excluded(exclude: Union[Set, Dict, None], key: str = None):
        # print(f'checking excluded for {key}', exclude)
        if isinstance(exclude, dict):
            if isinstance(exclude.get(key, {}), dict) and '__all__' in exclude.get(key, {}).keys():
                return exclude.get(key).get('__all__')
            return exclude.get(key, {})
        return exclude

    @staticmethod
    def is_excluded(exclude: Union[Set, Dict, None], key: str = None):
        if exclude is None:
            return False
        to_exclude = Excludable.get_excluded(exclude, key)
        # print(f'to exclude for current key = {key}', to_exclude)

        if isinstance(to_exclude, Set):
            return key in to_exclude
        elif to_exclude is ...:
            return True
        else:
            return False
