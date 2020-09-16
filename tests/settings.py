import os

os.environ['TEST_DATABASE_URLS'] = "sqlite:///test.db"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
