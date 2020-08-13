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
    album = orm.ForeignKey(Album, nullable=False)
    title = orm.String(length=100)
    position = orm.Integer()


album = await Album.objects.create(name="Brooklyn")
await Track.objects.create(album=album, title="The Bird", position=1)

# explicit preload of related Album Model
track = await Track.objects.select_related("album").get(title="The Bird")
assert track.album.name == 'Brooklyn'
# Will produce: True

# even without explicit select_related if ForeignKey is not nullable,
# the Album Model is still preloaded.
track2 = await Track.objects.get(title="The Bird")
assert track2.album.name == 'Brooklyn'
# Will produce: True
