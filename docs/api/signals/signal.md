<a name="signals.signal"></a>
# signals.signal

<a name="signals.signal.callable_accepts_kwargs"></a>
#### callable\_accepts\_kwargs

```python
callable_accepts_kwargs(func: Callable) -> bool
```

Checks if function accepts **kwargs.

**Arguments**:

- `func` (`function`): function which signature needs to be checked

**Returns**:

`bool`: result of the check

<a name="signals.signal.make_id"></a>
#### make\_id

```python
make_id(target: Any) -> Union[int, Tuple[int, int]]
```

Creates id of a function or method to be used as key to store signal

**Arguments**:

- `target` (`Any`): target which id we want

**Returns**:

`int`: id of the target

<a name="signals.signal.Signal"></a>
## Signal Objects

```python
class Signal()
```

Signal that notifies all receiver functions.
In ormar used by models to send pre_save, post_save etc. signals.

<a name="signals.signal.Signal.connect"></a>
#### connect

```python
 | connect(receiver: Callable) -> None
```

Connects given receiver function to the signal.

**Raises**:

- `SignalDefinitionError`: if receiver is not callable
or not accept **kwargs

**Arguments**:

- `receiver` (`Callable`): receiver function

<a name="signals.signal.Signal.disconnect"></a>
#### disconnect

```python
 | disconnect(receiver: Callable) -> bool
```

Removes the receiver function from the signal.

**Arguments**:

- `receiver` (`Callable`): receiver function

**Returns**:

`bool`: flag if receiver was removed

<a name="signals.signal.Signal.send"></a>
#### send

```python
 | async send(sender: Type["Model"], **kwargs: Any) -> None
```

Notifies all receiver functions with given kwargs

**Arguments**:

- `sender` (`Type["Model"]`): model that sends the signal
- `kwargs` (`Any`): arguments passed to receivers

<a name="signals.signal.SignalEmitter"></a>
## SignalEmitter Objects

```python
class SignalEmitter()
```

Emitter that registers the signals in internal dictionary.
If signal with given name does not exist it's auto added on access.

