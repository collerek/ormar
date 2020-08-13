import orm
import databases
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Album(orm.Model):
    __tablename__ = "album"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    name = orm.String(length=100)


class Track(orm.Model):
    __tablename__ = "track"
    __metadata__ = metadata
    __database__ = database

    id = orm.Integer(primary_key=True)
    album = orm.ForeignKey(Album)
    title = orm.String(length=100)
    position = orm.Integer()


print(Track.__table__.columns['album'].__repr__())
# Will produce:
# Column('album', Integer(), ForeignKey('album.id'), table=<track>)

print(Track.__pydantic_model__.__fields__['album'])
# Will produce:
# ModelField(
#   name='album'
#   type=Optional[Album]
#   required=False
#   default=None)
