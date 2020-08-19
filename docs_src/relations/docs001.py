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