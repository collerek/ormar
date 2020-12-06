from typing import Any, Callable, List, TYPE_CHECKING, Type, Union

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


def receiver(
    signal: str, senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    def _decorator(func: Callable) -> Callable:
        if not isinstance(senders, list):
            _senders = [senders]
        else:
            _senders = senders
        for sender in _senders:
            signals = getattr(sender.Meta.signals, signal)
            signals.connect(func, **kwargs)
        return func

    return _decorator


def post_save(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="post_save", senders=senders, **kwargs)


def post_update(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="post_update", senders=senders, **kwargs)


def post_delete(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="post_delete", senders=senders, **kwargs)


def pre_save(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="pre_save", senders=senders, **kwargs)


def pre_update(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="pre_update", senders=senders, **kwargs)


def pre_delete(
    senders: Union[Type["Model"], List[Type["Model"]]], **kwargs: Any
) -> Callable:
    return receiver(signal="pre_delete", senders=senders, **kwargs)
