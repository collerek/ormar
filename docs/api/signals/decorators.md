<a name="decorators.signals"></a>
# decorators.signals

<a name="decorators.signals.receiver"></a>
#### receiver

```python
receiver(signal: str, senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for given signal name.

**Arguments**:

- `signal (str)`: name of the signal to register to
- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.post_save"></a>
#### post\_save

```python
post_save(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for post_save signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.post_update"></a>
#### post\_update

```python
post_update(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for post_update signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.post_delete"></a>
#### post\_delete

```python
post_delete(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for post_delete signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.pre_save"></a>
#### pre\_save

```python
pre_save(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for pre_save signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.pre_update"></a>
#### pre\_update

```python
pre_update(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for pre_update signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.pre_delete"></a>
#### pre\_delete

```python
pre_delete(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for pre_delete signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.pre_relation_add"></a>
#### pre\_relation\_add

```python
pre_relation_add(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for pre_relation_add signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.post_relation_add"></a>
#### post\_relation\_add

```python
post_relation_add(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for post_relation_add signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.pre_relation_remove"></a>
#### pre\_relation\_remove

```python
pre_relation_remove(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for pre_relation_remove signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

<a name="decorators.signals.post_relation_remove"></a>
#### post\_relation\_remove

```python
post_relation_remove(senders: Union[Type["Model"], List[Type["Model"]]]) -> Callable
```

Connect given function to all senders for post_relation_remove signal.

**Arguments**:

- `senders (Union[Type["Model"], List[Type["Model"]]])`: one or a list of "Model" classes
that should have the signal receiver registered

**Returns**:

`(Callable)`: returns the original function untouched

