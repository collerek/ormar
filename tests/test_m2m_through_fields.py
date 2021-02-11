import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class PostCategory(ormar.Model):
    class Meta(BaseMeta):
        tablename = "posts_x_categories"

    id: int = ormar.Integer(primary_key=True)
    sort_order: int = ormar.Integer(nullable=True)


class Post(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories = ormar.ManyToMany(Category, through=PostCategory)


#
# @pytest.fixture(autouse=True, scope="module")
# async def create_test_database():
#     engine = sqlalchemy.create_engine(DATABASE_URL)
#     metadata.create_all(engine)
#     yield
#     metadata.drop_all(engine)
#
#
# @pytest.mark.asyncio
# async def test_setting_fields_on_through_model():
#     async with database:
#         # TODO: check/ modify following
#         # loading the data into model instance of though model?
#         # <- attach to other side? both sides? access by through, or add to fields?
#         # creating while adding to relation (kwargs in add?)
#         # creating in query (dividing kwargs between final and through)
#         # updating in query
#         # sorting in filter (special __through__<field_name> notation?)
#         # ordering by in order_by
#         # accessing from instance (both sides?)
#         # modifying from instance (both sides?)
#         # including/excluding in fields?
#         # allowing to change fk fields names in through model?
#         pass
