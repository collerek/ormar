To provide better errors check you should use mypy with pydantic [plugin][plugin] 

Please use notation introduced in version 0.4.0.

```Python hl_lines="16-18"
--8<-- "../docs_src/models/docs012.py"
```

Note that above example is not using the type hints, so further operations with mypy might fail, depending on the context.

Preferred notation should look liked this:

```Python hl_lines="16-18"
--8<-- "../docs_src/models/docs001.py"
```




[plugin]: https://pydantic-docs.helpmanual.io/mypy_plugin/