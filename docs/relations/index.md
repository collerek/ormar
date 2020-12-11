# Relations

Currently `ormar` supports two types of relations:

* One-to-many (and many-to-one) with `ForeignKey` field
* Many-to-many with `ManyToMany` field

Below you can find a very basic examples of definitions for each of those relations.

To read more about methods, possibilities, definition etc. please read the subsequent section of the documentation. 

## ForeignKey

To define many-to-one relation use `ForeignKey` field.

```Python hl_lines="17"
--8<-- "../docs_src/relations/docs003.py"
```

!!!tip
    To read more about one-to-many relations visit [foreign-keys][foreign-keys] section

## Reverse ForeignKey

The definition of one-to-many relation also uses `ForeignKey`, and it's registered for you automatically.

So in relation ato example above.

```Python hl_lines="17"
class Department(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # there is a virtual field here like follows
    courses: Optional[List[Course]] = ormar.ForeignKey(Course, virtual=True)
    # note that you DO NOT define it yourself, ormar does it for you.
```

!!!tip
    To read more about many-to-one relations (i.e changing the name of generated field) visit [foreign-keys][foreign-keys] section


!!!tip
    Reverse ForeignKey allows you to query the related models with [queryset-proxy][queryset-proxy].

##ManyToMany

To define many-to-many relation use `ManyToMany` field.


!!!tip
    To read more about many-to-many relations visit [many-to-many][many-to-many] section


!!!tip
    ManyToMany allows you to query the related models with [queryset-proxy][queryset-proxy].


[foreign-keys]: ./foreign-key.md
[many-to-many]: ./many-to-many.md
[queryset-proxy]: ./queryset-proxy.md