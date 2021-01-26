# Querying database with ormar

## QuerySet

Each Model is auto registered with a `QuerySet` that represents the underlying query,
and it's options.

Most of the methods are also available through many to many relations and on reverse
foreign key relations through `QuerysetProxy` interface.

!!!info To see which one are supported and how to construct relations
visit [relations][relations].

For simplicity available methods to fetch and save the data into the database are
divided into categories according to the function they fulfill.

Note that some functions/methods are in multiple categories.

For complicity also Models and relations methods are listed.

To read more about any specific section or function please refer to the details subpage.

### Create

* `create(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `update_or_create(**kwargs) -> Model`
* `bulk_create(objects: List[Model]) -> None`


* `Model`
  * `Model.save()` method
  * `Model.upsert()` method
  * `Model.save_related()` method


* `QuerysetProxy`
  * `QuerysetProxy.create(**kwargs)` method
  * `QuerysetProxy.get_or_create(**kwargs)` method
  * `QuerysetProxy.update_or_create(**kwargs)` method

### Read

* `get(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `first() -> Model`
* `all(**kwargs) -> List[Optional[Model]]`


* `Model`
    * `Model.load()` method


* `QuerysetProxy`
    * `QuerysetProxy.get(**kwargs)` method
    * `QuerysetProxy.get_or_create(**kwargs)` method
    * `QuerysetProxy.first()` method
    * `QuerysetProxy.all(**kwargs)` method

### Update

* `update(each: bool = False, **kwargs) -> int`
* `update_or_create(**kwargs) -> Model`
* `bulk_update(objects: List[Model], columns: List[str] = None) -> None`


* `Model`
    * `Model.update()` method
    * `Model.upsert()` method
    * `Model.save_related()` method


* `QuerysetProxy`
    * `QuerysetProxy.update_or_create(**kwargs)` method

### Delete

* `delete(each: bool = False, **kwargs) -> int`


* `Model`
    * `Model.delete()` method


* `QuerysetProxy`
    * `QuerysetProxy.remove()` method
    * `QuerysetProxy.clear()` method

### Joins and subqueries

* `select_related(related: Union[List, str]) -> QuerySet`
* `prefetch_related(related: Union[List, str]) -> QuerySet`


* `Model`
    * `Model.load()` method


* `QuerysetProxy`
    * `QuerysetProxy.select_related(related: Union[List, str])` method
    * `QuerysetProxy.prefetch_related(related: Union[List, str])` method

### Filtering and sorting

* `filter(**kwargs) -> QuerySet`
* `exclude(**kwargs) -> QuerySet`
* `order_by(columns:Union[List, str]) -> QuerySet`
* `get(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `all(**kwargs) -> List[Optional[Model]]`


* `QuerysetProxy`
    * `QuerysetProxy.filter(**kwargs)` method
    * `QuerysetProxy.exclude(**kwargs)` method
    * `QuerysetProxy.order_by(columns:Union[List, str])` method
    * `QuerysetProxy.get(**kwargs)` method
    * `QuerysetProxy.get_or_create(**kwargs)` method
    * `QuerysetProxy.all(**kwargs)` method

### Selecting columns

* `fields(columns: Union[List, str, set, dict]) -> QuerySet`
* `exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`


* `QuerysetProxy`
    * `QuerysetProxy.fields(columns: Union[List, str, set, dict])` method
    * `QuerysetProxy.exclude_fields(columns: Union[List, str, set, dict])` method

### Pagination and rows number

* `paginate(page: int) -> QuerySet`
* `limit(limit_count: int) -> QuerySet`
* `offset(offset: int) -> QuerySet`
* `get() -> Model`
* `first() -> Model`


* `QuerysetProxy`
    * `QuerysetProxy.paginate(page: int)` method
    * `QuerysetProxy.limit(limit_count: int)` method
    * `QuerysetProxy.offset(offset: int)` method

### Aggregated functions

* `count() -> int`
* `exists() -> bool`


* `QuerysetProxy`
    * `QuerysetProxy.count()` method
    * `QuerysetProxy.exists()` method
  

[relations]: ./relations/index.md