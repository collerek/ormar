import ormar
import databases
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class Album(ormar.Model):
    __tablename__ = "album"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    name = ormar.String(length=100)


class Track(ormar.Model):
    __tablename__ = "track"
    __metadata__ = metadata
    __database__ = database

    id = ormar.Integer(primary_key=True)
    album = ormar.ForeignKey(Album)
    title = ormar.String(length=100)
    position = ormar.Integer()


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
