base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)


class Category(ormar.Model):
    class Meta(BaseMeta):
        tablename = "categories"

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=40)


class PostCategory(ormar.Model):
    class Meta(BaseMeta):
        tablename = "posts_x_categories"

    id: int = ormar.Integer(primary_key=True)
    sort_order: int = ormar.Integer(nullable=True)
    param_name: str = ormar.String(default="Name", max_length=200)


class Post(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    categories = ormar.ManyToMany(Category, through=PostCategory)
