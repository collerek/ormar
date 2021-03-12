from typing import Callable, List, TYPE_CHECKING, Type, Union

if TYPE_CHECKING:  # pragma: no cover
    from ormar import Model


def receiver(
    signal: str, senders: Union[Type["Model"], List[Type["Model"]]]
) -> Callable:
    """
    Connect given function to all senders for given signal name.

    :param signal: name of the signal to register to
    :type signal: str
    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """

    def _decorator(func: Callable) -> Callable:
        """

        Internal decorator that does all the registering.

        :param func: function to register as receiver
        :type func: Callable
        :return: untouched function already registered for given signal
        :rtype: Callable
        """
        if not isinstance(senders, list):
            _senders = [senders]
        else:
            _senders = senders
        for sender in _senders:
            signals = getattr(sender.Meta.signals, signal)
            signals.connect(func)
        return func

    return _decorator


def post_save(senders: Union[Type["Model"], List[Type["Model"]]],) -> Callable:
    """
    Connect given function to all senders for post_save signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="post_save", senders=senders)


def post_update(senders: Union[Type["Model"], List[Type["Model"]]],) -> Callable:
    """
    Connect given function to all senders for post_update signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="post_update", senders=senders)


def post_delete(senders: Union[Type["Model"], List[Type["Model"]]],) -> Callable:
    """
    Connect given function to all senders for post_delete signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="post_delete", senders=senders)


def pre_save(senders: Union[Type["Model"], List[Type["Model"]]],) -> Callable:
    """
    Connect given function to all senders for pre_save signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="pre_save", senders=senders)


def pre_update(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable:
    """
    Connect given function to all senders for pre_update signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="pre_update", senders=senders)


def pre_delete(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable:
    """
    Connect given function to all senders for pre_delete signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="pre_delete", senders=senders)


def pre_relation_add(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable:
    """
    Connect given function to all senders for pre_relation_add signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="pre_relation_add", senders=senders)


def post_relation_add(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable:
    """
    Connect given function to all senders for post_relation_add signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="post_relation_add", senders=senders)


def pre_relation_remove(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable:
    """
    Connect given function to all senders for pre_relation_remove signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="pre_relation_remove", senders=senders)


def post_relation_remove(
    senders: Union[Type["Model"], List[Type["Model"]]]
) -> Callable:
    """
    Connect given function to all senders for post_relation_remove signal.

    :param senders: one or a list of "Model" classes
    that should have the signal receiver registered
    :type senders: Union[Type["Model"], List[Type["Model"]]]
    :return: returns the original function untouched
    :rtype: Callable
    """
    return receiver(signal="post_relation_remove", senders=senders)
