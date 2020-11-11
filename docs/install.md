## Installation

Installation is as simple as:

```py
pip install ormar
```

### Dependencies

Ormar uses `databases` for connectivity issues, `pydantic` for validation and `sqlalchemy-core` for queries.

All three should install along the installation of ormar if not present at your system before.

*  databases
*  pydantic>=1.5 
*  sqlalchemy 


## Optional dependencies

*ormar* has three optional dependencies based on database backend you use:

### Postgresql

```py
pip install ormar[postgresql]
```
Will install also `asyncpg` and `psycopg2`.

### Mysql

```py
pip install ormar[mysql]
```

Will install also `aiomysql` and `pymysql`.

### Sqlite

```py
pip install ormar[sqlite]
```

Will install also `aiosqlite`.

### Manual installation of dependencies

Of course, you can also install these requirements manually with `pip install asyncpg` etc.
