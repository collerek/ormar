import functools

import ormar


def create_drop_database(base_config: ormar.OrmarConfig) -> None:
    # create all tables in the database before execution
    # and drop them after, note that in production you should use migrations
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            # Connect database if not already connected
            if not base_config.database.is_connected:
                await base_config.database.connect()

            # Drop and create tables
            async with base_config.engine.begin() as conn:
                await conn.run_sync(base_config.metadata.drop_all)
                await conn.run_sync(base_config.metadata.create_all)

            try:
                await func(*args)
            finally:
                # Drop tables and cleanup
                async with base_config.engine.begin() as conn:
                    await conn.run_sync(base_config.metadata.drop_all)

                # Disconnect and dispose engine
                if base_config.database.is_connected:
                    await base_config.database.disconnect()
                await base_config.engine.dispose()

        return wrapped

    return wrapper
