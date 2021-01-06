"""
Signals and SignalEmitter that gathers the signals on models Meta.
Used to signal receivers functions about events, i.e. post_save, pre_delete etc.
"""
from ormar.signals.signal import Signal, SignalEmitter

__all__ = ["Signal", "SignalEmitter"]
