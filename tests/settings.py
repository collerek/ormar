import os

import databases
import ormar
import sqlalchemy

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
database_url = databases.DatabaseURL(DATABASE_URL)
if database_url.scheme == "postgresql+aiopg":  # pragma no cover
    DATABASE_URL = str(database_url.replace(driver=None))


def create_config(**args):
    database_ = databases.Database(DATABASE_URL, **args)
    metadata_ = sqlalchemy.MetaData()
    engine_ = sqlalchemy.create_engine(DATABASE_URL)

    return ormar.OrmarConfig(
        metadata=metadata_,
        database=database_,
        engine=engine_,
    )
