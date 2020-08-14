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
    album = ormar.ForeignKey(Album, nullable=False)
    title = ormar.String(length=100)
    position = ormar.Integer()


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
