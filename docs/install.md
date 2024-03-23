## Installation

Installation is as simple as:

```py
pip install ormar
```

### Dependencies

Ormar uses `databases` for connectivity issues, `pydantic` for validation and `sqlalchemy-core` for queries.

All three should install along the installation of ormar if not present at your system before.

*  databases
*  pydantic
*  sqlalchemy 

The required versions are pinned in the pyproject.toml file.

## Optional dependencies

*ormar* has three optional dependencies based on database backend you use:

### Database backend

#### Postgresql

```py
pip install ormar[postgresql]
```
Will install also `asyncpg` and `psycopg2`.

#### Mysql

```py
pip install ormar[mysql]
```

Will install also `aiomysql` and `pymysql`.

#### Sqlite

```py
pip install ormar[sqlite]
```

Will install also `aiosqlite`.

### Orjson

```py
pip install ormar[orjson]
```

Will install also `orjson` that is much faster than builtin json parser.

### Crypto

```py
pip install ormar[crypto]
```

Will install also `cryptography` that is required to work with encrypted columns.

### Manual installation of dependencies

Of course, you can also install these requirements manually with `pip install asyncpg` etc.
