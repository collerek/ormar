import os

import databases

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
database_url = databases.DatabaseURL(DATABASE_URL)
if database_url.scheme == "postgresql+aiopg":  # pragma no cover
    DATABASE_URL = str(database_url.replace(driver=None))
print("USED DB:", DATABASE_URL)
