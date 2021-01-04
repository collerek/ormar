import asyncio
import inspect
from typing import Any, Callable, Dict, List, TYPE_CHECKING, Tuple, Type, Union

from ormar.exceptions import SignalDefinitionError

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


def callable_accepts_kwargs(func: Callable) -> bool:
    """
    Checks if function accepts **kwargs.

    :param func: function which signature needs to be checked
    :type func: function
    :return: result of the check
    :rtype: bool
    """
    return any(
        p
        for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )


def make_id(target: Any) -> Union[int, Tuple[int, int]]:
    """
    Creates id of a function or method to be used as key to store signal

    :param target: target which id we want
    :type target: Any
    :return: id of the target
    :rtype: int
    """
    if hasattr(target, "__func__"):
        return id(target.__self__), id(target.__func__)
    return id(target)


class Signal:
    """
    Signal that notifies all receiver functions.
    In ormar used by models to send pre_save, post_save etc. signals.
    """

    def __init__(self) -> None:
        self._receivers: List[Tuple[Union[int, Tuple[int, int]], Callable]] = []

    def connect(self, receiver: Callable) -> None:
        """
        Connects given receiver function to the signal.

        :raises SignalDefinitionError: if receiver is not callable
        or not accept **kwargs
        :param receiver: receiver function
        :type receiver: Callable
        """
        if not callable(receiver):
            raise SignalDefinitionError("Signal receivers must be callable.")
        if not callable_accepts_kwargs(receiver):
            raise SignalDefinitionError(
                "Signal receivers must accept **kwargs argument."
            )
        new_receiver_key = make_id(receiver)
        if not any(rec_id == new_receiver_key for rec_id, _ in self._receivers):
            self._receivers.append((new_receiver_key, receiver))

    def disconnect(self, receiver: Callable) -> bool:
        """
        Removes the receiver function from the signal.

        :param receiver: receiver function
        :type receiver: Callable
        :return: flag if receiver was removed
        :rtype: bool
        """
        removed = False
        new_receiver_key = make_id(receiver)
        for ind, rec in enumerate(self._receivers):
            rec_id, _ = rec
            if rec_id == new_receiver_key:
                removed = True
                del self._receivers[ind]
                break
        return removed

    async def send(self, sender: Type["Model"], **kwargs: Any) -> None:
        """
        Notifies all receiver functions with given kwargs
        :param sender: model that sends the signal
        :type sender: Type["Model"]
        :param kwargs: arguments passed to receivers
        :type kwargs: Any
        """
        receivers = []
        for receiver in self._receivers:
            _, receiver_func = receiver
            receivers.append(receiver_func(sender=sender, **kwargs))
        await asyncio.gather(*receivers)


class SignalEmitter:
    """
    Emitter that registers the signals in internal dictionary.
    If signal with given name does not exist it's auto added on access.
    """

    if TYPE_CHECKING:  # pragma: no cover
        signals: Dict[str, Signal]

    def __init__(self) -> None:
        object.__setattr__(self, "signals", dict())

    def __getattr__(self, item: str) -> Signal:
        return self.signals.setdefault(item, Signal())

    def __setattr__(self, key: str, value: Any) -> None:
        signals = object.__getattribute__(self, "signals")
        signals[key] = value
