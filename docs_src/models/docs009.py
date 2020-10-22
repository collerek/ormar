class Album(ormar.Model):
    class Meta:
        tablename = "music_albums"
        metadata = metadata
        database = database

    id: ormar.Integer(name='album_id', primary_key=True)
    name: ormar.String(name='album_name', max_length=100)
    artist: ormar.ForeignKey(Artist, name='artist_id')
