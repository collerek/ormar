class ArtistChildren(ormar.Model):
    class Meta:
        tablename = "children_x_artists"
        metadata = metadata
        database = database


class Artist(ormar.Model):
    class Meta:
        tablename = "artists"
        metadata = metadata
        database = database

    id = ormar.Integer(name='artist_id', primary_key=True)
    first_name = ormar.String(name='fname', max_length=100)
    last_name = ormar.String(name='lname', max_length=100)
    born_year = ormar.Integer(name='year')
    children: Optional[Union[Child, List[Child]]] = ormar.ManyToMany(Child, through=ArtistChildren)
