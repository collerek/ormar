import os

import databases

assert "DATABASE_URL" in os.environ, "DATABASE_URL is not set."

DATABASE_URL = os.environ['DATABASE_URL']
database_url = databases.DatabaseURL(DATABASE_URL)
if database_url.scheme == "postgresql+aiopg":  # pragma no cover
    DATABASE_URL = str(database_url.replace(driver=None))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
