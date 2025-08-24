import functools

import ormar
import sqlalchemy


def create_drop_database(base_config: ormar.OrmarConfig) -> None:
    # create all tables in the database before execution
    # and drop them after, note that in production you should use migrations
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            engine = sqlalchemy.create_engine(str(base_config.database.url))
            base_config.metadata.drop_all(engine)
            base_config.metadata.create_all(engine)
            await func(*args)
            base_config.metadata.drop_all(engine)

        return wrapped

    return wrapper
