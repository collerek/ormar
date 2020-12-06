import asyncio
import inspect
from typing import Any, Callable, List, Tuple, Union

from ormar.exceptions import SignalDefinitionError


def callable_accepts_kwargs(func: Callable) -> bool:
    return any(
        p
        for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )


def make_id(target: Any) -> Union[int, Tuple[int, int]]:
    if hasattr(target, "__func__"):
        return id(target.__self__), id(target.__func__)
    return id(target)


class Signal:
    def __init__(self) -> None:
        self._receivers: List[Tuple[Union[int, Tuple[int, int]], Callable]] = []

    def connect(self, receiver: Callable) -> None:
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
        removed = False
        new_receiver_key = make_id(receiver)
        for ind, rec in enumerate(self._receivers):
            rec_id, _ = rec
            if rec_id == new_receiver_key:
                removed = True
                del self._receivers[ind]
                break
        return removed

    async def send(self, sender: Any, **kwargs: Any) -> None:
        receivers = []
        for receiver in self._receivers:
            _, receiver_func = receiver
            receivers.append(receiver_func(sender, **kwargs))
        await asyncio.gather(*receivers)
