# 0.12.0

## ✨ Breaking Changes

* `Queryset.bulk_create` will now raise `ModelListEmptyError` on empty list of models (by @ponytailer - thanks!) [#853](https://github.com/collerek/ormar/pull/853)

## ✨ Features
* `Model.upsert()` now handles a flag `__force_save__`: `bool` that allow upserting the models regardless of the fact if they have primary key set or not. 
Note that setting this flag will cause two queries for each upserted model -> `get` to check if model exists and later `update/insert` accordingly. [#889](https://github.com/collerek/ormar/pull/853)

## 🐛 Fixes

* Fix for empty relations breaking `construct` method (by @Abdeldjalil-H - thanks!) [#870](https://github.com/collerek/ormar/issues/870)
* Fix save related not saving models with already set pks (including uuid) [#885](https://github.com/collerek/ormar/issues/885)
* Fix for wrong relations exclusions depending on the order of exclusions [#779](https://github.com/collerek/ormar/issues/779)
* Fix `property_fields` not being inherited properly [#774](https://github.com/collerek/ormar/issues/774)

# 0.11.3

## ✨ Features

* Document `onupdate` and `ondelete` referential actions in `ForeignKey` and provide `ReferentialAction` enum to specify the behavior of the relationship (by @SepehrBazyar - thanks!) [#724](https://github.com/collerek/ormar/issues/724)
* Add `CheckColumn` to supported constraints in models Meta (by @SepehrBazyar - thanks!) [#729](https://github.com/collerek/ormar/issues/729)

## 🐛 Fixes

* Fix limiting query result to 0 should return empty list (by @SepehrBazyar - thanks!) [#766](https://github.com/collerek/ormar/issues/713)

## 💬 Other

* Add dark mode to docs (by @SepehrBazyar - thanks!) [#717](https://github.com/collerek/ormar/pull/717) 
* Update aiomysql dependency [#778](https://github.com/collerek/ormar/issues/778)


# 0.11.2

## 🐛 Fixes

* Fix database drivers being required, while they should be optional [#713](https://github.com/collerek/ormar/issues/713)
* Fix boolean field problem in `limit` queries in postgres without `limit_raw_sql` flag [#704](https://github.com/collerek/ormar/issues/704)
* Fix enum_class spilling to schema causing errors in OpenAPI [#699](https://github.com/collerek/ormar/issues/699)

# 0.11.1

## 🐛 Fixes

* Fix deepcopy issues introduced in pydantic 1.9 [#685](https://github.com/collerek/ormar/issues/685)

# 0.11.0

## ✨ Breaking Changes

* Dropped support for python 3.6
* `Queryset.get_or_create` returns now a tuple with model and bool value indicating if the model was created (by @MojixCoder - thanks!) [#554](https://github.com/collerek/ormar/pull/554)
* `Queryset.count()` now counts the number of distinct parent model rows by default, counting all rows is possible by setting `distinct=False` (by @erichaydel - thanks) [#588](https://github.com/collerek/ormar/pull/588)

## ✨ Features

* Added support for python 3.10

## 🐛 Fixes

* Fix inconsistent `JSON` fields behaviour in `save` and `bulk_create` [#584](https://github.com/collerek/ormar/issues/584)
* Fix maximum recursion error [#580](https://github.com/collerek/ormar/pull/580)


# 0.10.25

## ✨ Features

* Add `queryset_class` option to `Model.Meta` that allows you to easily swap `QuerySet` for your Model (by @ponytailer - thanks!) [#538](https://github.com/collerek/ormar/pull/538)
* Allow passing extra `kwargs` to `IndexColumns` that will be passed to sqlalchemy `Index` (by @zevisert - thanks) [#575](https://github.com/collerek/ormar/pull/538)

## 🐛 Fixes

* Fix nullable setting on `JSON` fields [#529](https://github.com/collerek/ormar/issues/529)
* Fix bytes/str mismatch in bulk operations when using orjson instead of json (by @ponytailer - thanks!) [#538](https://github.com/collerek/ormar/pull/538)

# 0.10.24

## ✨ Features

* Add `post_bulk_update` signal (by @ponytailer - thanks!) [#524](https://github.com/collerek/ormar/pull/524)

## 🐛 Fixes

* Fix support for `pydantic==1.9.0` [#502](https://github.com/collerek/ormar/issues/502)
* Fix timezone issues with datetime [#504](https://github.com/collerek/ormar/issues/504)
* Remove literal binds in query generation to unblock postgres arrays [#/tophat/ormar-postgres-extensions/9](https://github.com/tophat/ormar-postgres-extensions/pull/9)
* Fix bulk update for `JSON` fields [#519](https://github.com/collerek/ormar/issues/519)

## 💬 Other

* Improve performance of `bulk_create` by bypassing `databases` `execute_many` suboptimal implementation. (by @Mng-dev-ai thanks!) [#520](https://github.com/collerek/ormar/pull/520) 
* Bump min. required `databases` version to `>=5.4`.

# 0.10.23

## ✨ Features

* Add ability to pass `comment` to sqlalchemy when creating a column [#485](https://github.com/collerek/ormar/issues/485)

## 🐛 Fixes

* Fix `LargeBinary` fields that can be nullable [#409](https://github.com/collerek/ormar/issues/409)
* Make `ormar.Model` pickable [#413](https://github.com/collerek/ormar/issues/413)
* Make `first()` and `get()` without arguments respect ordering of main model set by user, fallback to primary key (asc, and desc respectively) [#453](https://github.com/collerek/ormar/issues/453)
* Fix improper quoting of non-aliased join `on` clauses in postgress [#455](https://github.com/collerek/ormar/issues/455)

# 0.10.22

## 🐛 Fixes

* Hot fix for validators not being inherited when parent `ormar` model was set [#365](https://github.com/collerek/ormar/issues/365)


# 0.10.21

## 🐛 Fixes

* Add `ormar` implementation of `construct` classmethod that allows to build `Model` instances without validating the input to speed up the whole flow, if your data is already validated [#318](https://github.com/collerek/ormar/issues/318)
* Fix for "inheriting" field validators from `ormar` model when newly created pydanic model is generated with `get_pydantic` [#365](https://github.com/collerek/ormar/issues/365)

# 0.10.20

## ✨ Features

* Add `extra` parameter in `Model.Meta` that accepts `Extra.ignore` and `Extra.forbid` (default) and either ignores the extra fields passed to `ormar` model or raises an exception if one is encountered [#358](https://github.com/collerek/ormar/issues/358)

## 🐛 Fixes

* Allow `None` if field is nullable and have choices set [#354](https://github.com/collerek/ormar/issues/354)
* Always set `primary_key` to `not null` regardless of `autoincrement` and explicit `nullable` setting to avoid problems with migrations [#348](https://github.com/collerek/ormar/issues/348) 

# 0.10.19

## ✨ Features

* Add support for multi-column non-unique `IndexColumns` in `Meta.constraints` [#307](https://github.com/collerek/ormar/issues/307)
* Add `sql_nullable` field attribute that allows to set different nullable setting for pydantic model and for underlying sql column [#308](https://github.com/collerek/ormar/issues/308)

## 🐛 Fixes

* Enable caching of relation map to increase performance [#337](https://github.com/collerek/ormar/issues/337)
* Clarify and fix documentation in regard of nullable fields [#339](https://github.com/collerek/ormar/issues/339)

## 💬 Other

* Bump supported `databases` version to `<=5.2`.



# 0.10.18

## 🐛 Fixes

* Fix order of fields in pydantic models [#328](https://github.com/collerek/ormar/issues/328)
* Fix databases 0.5.0 support [#142](https://github.com/collerek/ormar/issues/142)

# 0.10.17

## ✨ Features

* Allow overwriting the default pydantic type for model fields [#312](https://github.com/collerek/ormar/issues/312)
* Add support for `sqlalchemy` >=1.4 (requires `databases` >= 0.5.0) [#142](https://github.com/collerek/ormar/issues/142)

# 0.10.16

## ✨ Features

* Allow passing your own pydantic `Config` to `ormar.Model` that will be merged with the default one by @naturalethic (thanks!) [#285](https://github.com/collerek/ormar/issues/285)
* Add `SmallInteger` field type by @ProgrammerPlus1998 (thanks!) [#297](https://github.com/collerek/ormar/pull/297)


## 🐛 Fixes

* Fix generating openapi schema by removing obsolete pydantic field parameters that were directly exposed in schema [#291](https://github.com/collerek/ormar/issues/291)
* Fix unnecessary warning for auto generated through models [#295](https://github.com/collerek/ormar/issues/295)



# 0.10.15

## 🐛 Fixes

* Fix generating pydantic models tree with nested models (by @pawamoy - thanks!) [#278](https://github.com/collerek/ormar/issues/278)
* Fix missing f-string in warning about missing primary key field [#274](https://github.com/collerek/ormar/issues/274)
* Fix passing foreign key value as relation (additional guard, fixed already in the latest release) [#270](https://github.com/collerek/ormar/issues/270)


# 0.10.14

## ✨ Features

* Allow passing `timezone:bool = False` parameter to `DateTime` and `Time` fields for timezone aware database columns [#264](https://github.com/collerek/ormar/issues/264)
* Allow passing datetime, date and time for filter on `DateTime`, `Time` and `Date` fields to allow filtering by datetimes instead of converting the value to string [#79](https://github.com/collerek/ormar/issues/79)

## 🐛 Fixes

* Fix dependencies from `psycopg2` to `psycopg2-binary` [#255](https://github.com/collerek/ormar/issues/255)


# 0.10.13

## ✨ Features

* Allow passing field accessors in `select_related` and `prefetch_related` aka. python style `select_related` [#225](https://github.com/collerek/ormar/issues/225).
  *  Previously: 
  ```python
    await Post.objects.select_related(["author", "categories"]).get()
    await Author.objects.prefetch_related("posts__categories").get()
  ```
  * Now also:
  ```python
    await Post.objects.select_related([Post.author, Post.categories]).get()
    await Author.objects.prefetch_related(Author.posts.categories).get()
  ```

## 🐛 Fixes

* Fix overwriting default value for inherited primary key [#253](https://github.com/collerek/ormar/issues/253)

# 0.10.12

## 🐛 Fixes

* Fix `QuerySet.create` method not using init (if custom provided) [#245](https://github.com/collerek/ormar/issues/245)
* Fix `ForwardRef` `ManyToMany` relation setting wrong pydantic type [#250](https://github.com/collerek/ormar/issues/250)


# 0.10.11

## ✨ Features

* Add `values` and `values_list` to `QuerySet` and `QuerysetProxy` that allows to return raw data from query [#223](https://github.com/collerek/ormar/issues/223).
  * Allow returning list of tuples or list of dictionaries from a query
  * Skips parsing the data to ormar model so skips also the validation
  * Allow excluding models in between in chain of relations, so you can extract only needed columns
  * `values_list` allows you to flatten the result if you extract only one column.

## 🐛 Fixes

* Fix creation of auto through model for m2m relation with ForwardRef [#226](https://github.com/collerek/ormar/issues/226)

# 0.10.10

## ✨ Features

* Add [`get_pydantic`](https://collerek.github.io/ormar/models/methods/#get_pydantic) flag that allows you to auto generate equivalent pydantic models tree from ormar.Model. This newly generated model tree can be used in requests and responses to exclude fields you do not want to include in the data.
* Add [`exclude_parent_fields`](https://collerek.github.io/ormar/models/inheritance/#exclude_parent_fields) parameter to model Meta that allows you to exclude fields from parent models during inheritance. Note that best practice is to combine models and mixins but if you have many similar models and just one that differs it might be useful tool to achieve that. 

## 🐛 Fixes

* Fix is null filter with pagination and relations (by @erichaydel) [#214](https://github.com/collerek/ormar/issues/214)
* Fix not saving child object on reverse side of the relation if not saved before [#216](https://github.com/collerek/ormar/issues/216)


## 💬 Other

* Expand [fastapi](https://collerek.github.io/ormar/fastapi) part of the documentation to show samples of using ormar in requests and responses in fastapi.
* Improve the docs in regard of `default`, `ForeignKey.add` etc. 

# 0.10.9

## Important security fix

*  Update pin for pydantic to fix security vulnerability [CVE-2021-29510](https://github.com/samuelcolvin/pydantic/security/advisories/GHSA-5jqp-qgf6-3pvh)

You are advised to update to version of pydantic that was patched. 
In 0.10.9 ormar excludes versions with vulnerability in pinned dependencies. 

## 🐛 Fixes

* Fix OpenAPi schema for LargeBinary [#204](https://github.com/collerek/ormar/issues/204)

# 0.10.8

## 🐛 Fixes

* Fix populating default values in pk_only child models [#202](https://github.com/collerek/ormar/issues/202)
* Fix mypy for LargeBinary fields with base64 str representation [#199](https://github.com/collerek/ormar/issues/199)
* Fix OpenAPI schema format for LargeBinary fields with base64 str representation [#199](https://github.com/collerek/ormar/issues/199)
* Fix OpenAPI choices encoding for LargeBinary fields with base64 str representation

# 0.10.7

## ✨ Features

* Add `exclude_primary_keys: bool = False` flag to `dict()` method that allows to exclude all primary key columns in the resulting dictionaru. [#164](https://github.com/collerek/ormar/issues/164)
* Add `exclude_through_models: bool = False` flag to `dict()` that allows excluding all through models from `ManyToMany` relations [#164](https://github.com/collerek/ormar/issues/164)
* Add `represent_as_base64_str: bool = False` parameter that allows conversion of bytes `LargeBinary` field to base64 encoded string. String is returned in `dict()`, 
  on access to attribute and string is converted to bytes on setting. Data in database is stored as bytes. [#187](https://github.com/collerek/ormar/issues/187)
* Add `pk` alias to allow field access by `Model.pk` in filters and order by clauses (python style)

## 🐛 Fixes

* Remove default `None` option for `max_length` for `LargeBinary` field [#186](https://github.com/collerek/ormar/issues/186)
* Remove default `None` option for `max_length` for `String` field

## 💬 Other

* Provide a guide and samples of `dict()` parameters in the [docs](https://collerek.github.io/ormar/models/methods/)
* Major refactor of getting/setting attributes from magic methods into descriptors -> noticeable performance improvement

# 0.10.6

## ✨ Features

* Add `LargeBinary(max_length)` field type [#166](https://github.com/collerek/ormar/issues/166)
* Add support for normal pydantic fields (including Models) instead of `pydantic_only` 
  attribute which is now deprecated [#160](https://github.com/collerek/ormar/issues/160).
  Pydantic fields should be declared normally as in pydantic model next to ormar fields, 
  note that (obviously) `ormar` does not save and load the value for this field in 
  database that mean that **ONE** of the following has to be true:
  
    * pydantic field declared on ormar model has to be `Optional` (defaults to None)
    * pydantic field has to have a default value set
    * pydantic field has `default_factory` function set
    * ormar.Model with pydantic field has to overwrite `__init__()` and provide the value there
    
    If none of the above `ormar` (or rather pydantic) will fail during loading data from the database,
    with missing required value for declared pydantic field.
* Ormar provides now a meaningful examples in openapi schema, including nested models.
  The same algorithm is used to iterate related models without looks 
  as with `dict()` and `select/load_all`. Examples appear also in `fastapi`. [#157](https://github.com/collerek/ormar/issues/157)

## 🐛 Fixes

* By default `pydantic` is not validating fields during assignment, 
  which is not a desirable setting for an ORM, now all `ormar.Models` 
  have validation turned-on during assignment (like `model.column = 'value'`)

## 💬 Other

*  Add connecting to the database in QuickStart in readme [#180](https://github.com/collerek/ormar/issues/180) 
*  OpenAPI schema does no longer include `ormar.Model` docstring as description, 
   instead just model name is provided if you do not provide your own docstring.
*  Some performance improvements.

# 0.10.5

## 🐛 Fixes

*  Fix bug in `fastapi-pagination` [#73](https://github.com/uriyyo/fastapi-pagination/issues/73)
*  Remove unnecessary `Optional` in `List[Optional[T]]` in return value for `QuerySet.all()` and `Querysetproxy.all()` return values [#174](https://github.com/collerek/ormar/issues/174)
*  Run tests coverage publish only on internal prs instead of all in github action.

# 0.10.4

## ✨ Features

* Add **Python style** to `filter` and `order_by` with field access instead of dunder separated strings. [#51](https://github.com/collerek/ormar/issues/51)
  * Accessing a field with attribute access (chain of dot notation) can be used to construct `FilterGroups` (`ormar.and_` and `ormar.or_`)
  * Field access overloads set of python operators and provide a set of functions to allow same functionality as with dunder separated param names in `**kwargs`, that means that querying from sample model `Track` related to model `Album` now you have more options:
    *  exact - exact match to value, sql `column = <VALUE>` 
       * OLD: `album__name__exact='Malibu'`
       * NEW: can be also written as `Track.album.name == 'Malibu`
    *  iexact - exact match sql `column = <VALUE>` (case insensitive)
       * OLD: `album__name__iexact='malibu'`
       * NEW: can be also written as `Track.album.name.iexact('malibu')`
    *  contains - sql `column LIKE '%<VALUE>%'`
       * OLD: `album__name__contains='Mal'`
       * NEW: can be also written as `Track.album.name % 'Mal')`
       * NEW: can be also written as `Track.album.name.contains('Mal')`
    *  icontains - sql `column LIKE '%<VALUE>%'` (case insensitive)
       * OLD: `album__name__icontains='mal'`
       * NEW: can be also written as `Track.album.name.icontains('mal')`
    *  in - sql ` column IN (<VALUE1>, <VALUE2>, ...)`
       * OLD: `album__name__in=['Malibu', 'Barclay']`
       * NEW: can be also written as `Track.album.name << ['Malibu', 'Barclay']`
       * NEW: can be also written as `Track.album.name.in_(['Malibu', 'Barclay'])`
    *  isnull - sql `column IS NULL` (and sql `column IS NOT NULL`) 
       * OLD: `album__name__isnull=True` (isnotnull `album__name__isnull=False`)
       * NEW: can be also written as `Track.album.name >> None`
       * NEW: can be also written as `Track.album.name.isnull(True)`
       * NEW: not null can be also written as `Track.album.name.isnull(False)`
       * NEW: not null can be also written as `~(Track.album.name >> None)`
       * NEW: not null can be also written as `~(Track.album.name.isnull(True))`
    *  gt - sql `column > <VALUE>` (greater than)
       * OLD: `position__gt=3`
       * NEW: can be also written as `Track.album.name > 3`
    *  gte - sql `column >= <VALUE>` (greater or equal than)
       * OLD: `position__gte=3`
       * NEW: can be also written as `Track.album.name >= 3`
    *  lt - sql `column < <VALUE>` (lower than)
       * OLD: `position__lt=3`
       * NEW: can be also written as `Track.album.name < 3`
    *  lte - sql `column <= <VALUE>` (lower equal than)
       * OLD: `position__lte=3` 
       * NEW: can be also written as `Track.album.name <= 3`
    *  startswith - sql `column LIKE '<VALUE>%'` (exact start match)
       * OLD: `album__name__startswith='Mal'`
       * NEW: can be also written as `Track.album.name.startswith('Mal')`
    *  istartswith - sql `column LIKE '<VALUE>%'` (case insensitive)
       * OLD: `album__name__istartswith='mal'`
       * NEW: can be also written as `Track.album.name.istartswith('mal')`
    *  endswith - sql `column LIKE '%<VALUE>'` (exact end match)
       * OLD: `album__name__endswith='ibu'`
       * NEW: can be also written as `Track.album.name.endswith('ibu')`
    *  iendswith - sql `column LIKE '%<VALUE>'` (case insensitive)
       * OLD: `album__name__iendswith='IBU'` 
       * NEW: can be also written as `Track.album.name.iendswith('IBU')`
* You can provide `FilterGroups` not only in `filter()` and `exclude()` but also in:
  * `get()`
  * `get_or_none()`
  * `get_or_create()`
  * `first()`
  * `all()`
  * `delete()`
* With `FilterGroups` (`ormar.and_` and `ormar.or_`) you can now use: 
  *  `&` - as `and_` instead of next level of nesting
  *  `|` - as `or_' instead of next level of nesting
  *  `~` - as negation of the filter group
* To combine groups of filters into one set of conditions use `&` (sql `AND`) and `|` (sql `OR`)
  ```python
  # Following queries are equivalent:
  # sql: ( product.name = 'Test'  AND  product.rating >= 3.0 ) 
  
  # ormar OPTION 1 - OLD one
  Product.objects.filter(name='Test', rating__gte=3.0).get()
  
  # ormar OPTION 2 - OLD one
  Product.objects.filter(ormar.and_(name='Test', rating__gte=3.0)).get()
  
  # ormar OPTION 3 - NEW one (field access)
  Product.objects.filter((Product.name == 'Test') & (Product.rating >=3.0)).get()
  ```
* Same applies to nested complicated filters
  ```python
  # Following queries are equivalent:
  # sql: ( product.name = 'Test' AND product.rating >= 3.0 ) 
  #       OR (categories.name IN ('Toys', 'Books'))
  
  # ormar OPTION 1 - OLD one
  Product.objects.filter(ormar.or_(
                            ormar.and_(name='Test', rating__gte=3.0), 
                            categories__name__in=['Toys', 'Books'])
                        ).get()
  
  # ormar OPTION 2 - NEW one (instead of nested or use `|`)
  Product.objects.filter(
                        ormar.and_(name='Test', rating__gte=3.0) | 
                        ormar.and_(categories__name__in=['Toys', 'Books'])
                        ).get()
  
  # ormar OPTION 3 - NEW one (field access)
  Product.objects.filter(
                        ((Product.name='Test') & (Product.rating >= 3.0)) | 
                        (Product.categories.name << ['Toys', 'Books'])
                        ).get()
  ```
* Now you can also use field access to provide OrderActions to `order_by()`
  * Order ascending:
    * OLD: `Product.objects.order_by("name").all()`
    * NEW: `Product.objects.order_by(Product.name.asc()).all()`  
  * Order descending:
    * OLD: `Product.objects.order_by("-name").all()`
    * NEW: `Product.objects.order_by(Product.name.desc()).all()`
  * You can of course also combine different models and many order_bys:
    `Product.objects.order_by([Product.category.name.asc(), Product.name.desc()]).all()`

## 🐛 Fixes

*  Not really a bug but rather inconsistency. Providing a filter with nested model i.e. `album__category__name = 'AA'` 
   is checking if album and category models are included in `select_related()` and if not it's auto-adding them there.
   The same functionality was not working for `FilterGroups` (`and_` and `or_`), now it works (also for python style filters which return `FilterGroups`).

# 0.10.3

## ✨ Features

* `ForeignKey` and `ManyToMany` now support `skip_reverse: bool = False` flag [#118](https://github.com/collerek/ormar/issues/118).
  If you set `skip_reverse` flag internally the field is still registered on the other 
  side of the relationship so you can:
  * `filter` by related models fields from reverse model
  * `order_by` by related models fields from reverse model 
  
  But you cannot:
  * access the related field from reverse model with `related_name`
  * even if you `select_related` from reverse side of the model the returned models won't be populated in reversed instance (the join is not prevented so you still can `filter` and `order_by`)
  * the relation won't be populated in `dict()` and `json()`
  * you cannot pass the nested related objects when populating from `dict()` or `json()` (also through `fastapi`). It will be either ignored or raise error depending on `extra` setting in pydantic `Config`.
* `Model.save_related()` now can save whole data tree in once [#148](https://github.com/collerek/ormar/discussions/148)
  meaning:
  * it knows if it should save main `Model` or related `Model` first to preserve the relation
  * it saves main `Model` if 
    * it's not `saved`,
    * has no `pk` value 
    * or `save_all=True` flag is set 
  
    in those cases you don't have to split save into two calls (`save()` and `save_related()`)
  * it supports also `ManyToMany` relations
  * it supports also optional `Through` model values for m2m relations
*  Add possibility to customize `Through` model relation field names.
  * By default `Through` model relation names default to related model name in lowercase.
    So in example like this:
    ```python
    ... # course declaration ommited
    class Student(ormar.Model):
        class Meta:
            database = database
            metadata = metadata
    
        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)
        courses = ormar.ManyToMany(Course)
    
    # will produce default Through model like follows (example simplified)
    class StudentCourse(ormar.Model):
        class Meta:
            database = database
            metadata = metadata
            tablename = "students_courses"
    
        id: int = ormar.Integer(primary_key=True)
        student = ormar.ForeignKey(Student) # default name
        course = ormar.ForeignKey(Course)  # default name
    ```
  * To customize the names of fields/relation in Through model now you can use new parameters to `ManyToMany`:
    * `through_relation_name` - name of the field leading to the model in which `ManyToMany` is declared
    * `through_reverse_relation_name` - name of the field leading to the model to which `ManyToMany` leads to
    
    Example:
    ```python
    ... # course declaration ommited
    class Student(ormar.Model):
        class Meta:
            database = database
            metadata = metadata
    
        id: int = ormar.Integer(primary_key=True)
        name: str = ormar.String(max_length=100)
        courses = ormar.ManyToMany(Course,
                                   through_relation_name="student_id",
                                   through_reverse_relation_name="course_id")
    
    # will produce default Through model like follows (example simplified)
    class StudentCourse(ormar.Model):
        class Meta:
            database = database
            metadata = metadata
            tablename = "students_courses"
    
        id: int = ormar.Integer(primary_key=True)
        student_id = ormar.ForeignKey(Student) # set by through_relation_name
        course_id = ormar.ForeignKey(Course)  # set by through_reverse_relation_name
    ```  

## 🐛 Fixes

*  Fix weakref `ReferenceError` error [#118](https://github.com/collerek/ormar/issues/118)
*  Fix error raised by Through fields when pydantic `Config.extra="forbid"` is set
*  Fix bug with `pydantic.PrivateAttr` not being initialized at `__init__` [#149](https://github.com/collerek/ormar/issues/149)
*  Fix bug with pydantic-type `exclude` in `dict()` with `__all__` key not working

## 💬 Other
*  Introduce link to `sqlalchemy-to-ormar` auto-translator for models
*  Provide links to fastapi ecosystem libraries that support `ormar`
*  Add transactions to docs (supported with `databases`)


# 0.10.2

## ✨ Features

* `Model.save_related(follow=False)` now accept also two additional arguments: `Model.save_related(follow=False, save_all=False, exclude=None)`.
  *  `save_all:bool` -> By default (so with `save_all=False`) `ormar` only upserts models that are not saved (so new or updated ones), 
  with `save_all=True` all related models are saved, regardless of `saved` status, which might be useful if updated
  models comes from api call, so are not changed in the backend.
  *  `exclude: Union[Set, Dict, None]` -> set/dict of relations to exclude from save, those relation won't be saved even with `follow=True` and `save_all=True`. 
     To exclude nested relations pass a nested dictionary like: `exclude={"child":{"sub_child": {"exclude_sub_child_realtion"}}}`. The allowed values follow
     the `fields/exclude_fields` (from `QuerySet`) methods schema so when in doubt you can refer to docs in queries -> selecting subset of fields -> fields.
*  `Model.update()` method now accepts `_columns: List[str] = None` parameter, that accepts list of column names to update. If passed only those columns will be updated in database.
   Note that `update()` does not refresh the instance of the Model, so if you change more columns than you pass in `_columns` list your Model instance will have different values than the database!
*  `Model.dict()` method previously included only directly related models or nested models if they were not nullable and not virtual, 
   now all related models not previously visited without loops are included in `dict()`. This should be not breaking
   as just more data will be dumped to dict, but it should not be missing.
*  `QuerySet.delete(each=False, **kwargs)` previously required that you either pass a `filter` (by `**kwargs` or as a separate `filter()` call) or set `each=True` now also accepts
    `exclude()` calls that generates NOT filter. So either `each=True` needs to be set to delete whole table or at least one of `filter/exclude` clauses.
*  Same thing applies to `QuerySet.update(each=False, **kwargs)` which also previously required that you either pass a `filter` (by `**kwargs` or as a separate `filter()` call) or set `each=True` now also accepts
    `exclude()` calls that generates NOT filter. So either `each=True` needs to be set to update whole table or at least one of `filter/exclude` clauses.
*  Same thing applies to `QuerysetProxy.update(each=False, **kwargs)` which also previously required that you either pass a `filter` (by `**kwargs` or as a separate `filter()` call) or set `each=True` now also accepts
    `exclude()` calls that generates NOT filter. So either `each=True` needs to be set to update whole table or at least one of `filter/exclude` clauses.

## 🐛 Fixes

*  Fix improper relation field resolution in `QuerysetProxy` if fk column has different database alias.
*  Fix hitting recursion error with very complicated models structure with loops when calling `dict()`.
*  Fix bug when two non-relation fields were merged (appended) in query result when they were not relation fields (i.e. JSON)
*  Fix bug when during translation to dict from list the same relation name is used in chain but leads to different models
*  Fix bug when bulk_create would try to save also `property_field` decorated methods and `pydantic` fields
*  Fix wrong merging of deeply nested chain of reversed relations

## 💬 Other

*  Performance optimizations
*  Split tests into packages based on tested area

# 0.10.1

## Features

* add `get_or_none(**kwargs)` method to `QuerySet` and `QuerysetProxy`. It is exact equivalent of `get(**kwargs)` but instead of raising `ormar.NoMatch` exception if there is no db record matching the criteria, `get_or_none` simply returns `None`.
  
## Fixes

*  Fix dialect dependent quoting of column and table names in order_by clauses not working
   properly in postgres.

# 0.10.0

## Breaking

*  Dropped supported for long deprecated notation of field definition in which you use ormar fields as type hints i.e. `test_field: ormar.Integger() = None`
*  Improved type hints -> `mypy` can properly resolve related models fields (`ForeignKey` and `ManyToMany`) as well as return types of `QuerySet` methods. 
   Those mentioned are now returning proper model (i.e. `Book`) instead or `ormar.Model` type. There is still problem with reverse sides of relation and `QuerysetProxy` methods, 
   to ease type hints now those return `Any`. Partially fixes #112.

## Features

* add `select_all(follow: bool = False)` method to `QuerySet` and `QuerysetProxy`. 
  It is kind of equivalent of the Model's `load_all()` method but can be used directly in a query.
  By default `select_all()` adds only directly related models, with `follow=True` also related models
  of related models are added without loops in relations. Note that it's not and end `async` model
  so you still have to issue `get()`, `all()` etc. as `select_all()` returns a QuerySet (or proxy)
  like `fields()` or `order_by()`.

## Internals

*  `ormar` fields are no longer stored as classes in `Meta.model_fields` dictionary 
   but instead they are stored as instances.

# 0.9.9

## Features
*  Add possibility to change default ordering of relations and models.
    * To change model sorting pass `orders_by = [columns]` where `columns: List[str]` to model `Meta` class
    * To change relation order_by pass `orders_by = [columns]` where `columns: List[str]`
    * To change reverse relation order_by pass `related_orders_by = [columns]` where `columns: List[str]`
    * Arguments can be column names or `-{col_name}` to sort descending
    * In relations you can sort only by directly related model columns 
      or for `ManyToMany` columns also `Through` model columns `"{through_field_name}__{column_name}"`
    * Order in which order_by clauses are applied is as follows:
      * Explicitly passed `order_by()` calls in query
      * Relation passed `orders_by` if exists
      * Model `Meta` class `orders_by`
      * Model primary key column asc (fallback, used if none of above provided)
*  Add 4 new aggregated functions -> `min`, `max`, `sum` and `avg` that are their 
   corresponding sql equivalents. 
    *  You can pass one or many column names including related columns.
    *  As of now each column passed is aggregated separately (so `sum(col1+col2)` is not possible, 
       you can have `sum(col1, col2)` and later add 2 returned sums in python)
    *  You cannot `sum` and `avg` non numeric columns
    *  If you aggregate on one column, the single value is directly returned as a result
    *  If you aggregate on multiple columns a dictionary with column: result pairs is returned
*  Add 4 new signals -> `pre_relation_add`, `post_relation_add`, `pre_relation_remove` and `post_relation_remove`
    *  The newly added signals are emitted for `ManyToMany` relations (both sides) 
       and reverse side of `ForeignKey` relation (same as `QuerysetProxy` is exposed).
    *  Signals recieve following args: `sender: Type[Model]` - sender class, 
       `instance: Model` - instance to which related model is added, `child: Model` - model being added,
       `relation_name: str` - name of the relation to which child is added, 
       for add signals also `passed_kwargs: Dict` - dict of kwargs passed to `add()`

## Changes
* `Through` models for ManyToMany relations are now instantiated on creation, deletion and update, so you can provide not only
  autoincrement int as a primary key but any column type with default function provided.
* Since `Through` models are now instantiated you can also subscribe to `Through` model 
  pre/post save/update/delete signals
* `pre_update` signals receivers now get also passed_args argument which is a 
  dict of values passed to update function if any (else empty dict)
  
## Fixes
* `pre_update` signal now is sent before the extraction of values so you can modify the passed
  instance in place and modified fields values will be reflected in database
* `bulk_update` now works correctly also with `UUID` primary key column type


# 0.9.8

## Features
* Add possibility to encrypt the selected field(s) in the database
  * As minimum you need to provide `encrypt_secret` and `encrypt_backend`
  * `encrypt_backend` can be one of the `ormar.EncryptBackends` enum (`NONE, FERNET, HASH, CUSTOM`) - default: `NONE`
  * When custom backend is selected you need to provide your backend class that subclasses `ormar.fields.EncryptBackend`
  * You cannot encrypt `primary_key` column and relation columns (FK and M2M).
  * Provided are 2 backends: HASH and FERNET
    * HASH is a one-way hash (like for password), never decrypted on retrieval
    * FERNET is a two-way encrypt/decrypt backend
  * Note that in FERNET backend you loose `filtering` possibility altogether as part of the encrypted value is a timestamp.
  * Note that in HASH backend you can filter by full value but filters like `contain` will not work as comparison is make on encrypted values
  * Note that adding `encrypt_backend` changes the database column type to `TEXT`, which needs to be reflected in db either by migration or manual change

## Fixes
* (Advanced/ Internal) Restore custom sqlalchemy types (by `types.TypeDecorator` subclass) functionality that ceased to working so `process_result_value` was never called

# 0.9.7

## Features
* Add `isnull` operator to filter and exclude methods. 
    ```python
    album__name__isnull=True #(sql: album.name is null)
    album__name__isnull=False #(sql: album.name is not null))
    ```
* Add `ormar.or_` and `ormar.and_` functions that can be used to compose
  complex queries with nested conditions. 
  Sample query:
  ```python
  books = (
      await Book.objects.select_related("author")
      .filter(
          ormar.and_(
              ormar.or_(year__gt=1960, year__lt=1940),
              author__name="J.R.R. Tolkien",
          )
      )
      .all()
  )
  ```
  Check the updated docs in Queries -> Filtering and sorting -> Complex filters

## Other
* Setting default on `ForeignKey` or `ManyToMany` raises and `ModelDefinition` exception as it is (and was) not supported

# 0.9.6

##Important
* `Through` model for `ManyToMany` relations now **becomes optional**. It's not a breaking change
  since if you provide it everything works just fine as it used to. So if you don't want or need any additional 
  fields on `Through` model you can skip it. Note that it's going to be created for you automatically and 
  still has to be included in example in `alembic` migrations. 
  If you want to delete existing one check the default naming convention to adjust your existing database structure.

  Note that you still need to provide it if you want to 
  customize the `Through` model name or the database table name.

## Features
* Add `update` method to `QuerysetProxy` so now it's possible to update related models directly from parent model
  in `ManyToMany` relations and in reverse `ForeignKey` relations. Note that update like in `QuerySet` `update` returns number of
  updated models and **does not update related models in place** on parent model. To get the refreshed data on parent model you need to refresh
  the related models (i.e. `await model_instance.related.all()`)
* Add `load_all(follow=False, exclude=None)` model method that allows to load current instance of the model
  with all related models in one call. By default it loads only directly related models but setting
  `follow=True` causes traversing the tree (avoiding loops). You can also pass `exclude` parameter
  that works the same as `QuerySet.exclude_fields()` method.
* Added possibility to add more fields on `Through` model for `ManyToMany` relationships:
    * name of the through model field is the lowercase name of the Through class
    * you can pass additional fields when calling `add(child, **kwargs)` on relation (on `QuerysetProxy`)
    * you can pass additional fields when calling `create(**kwargs)` on relation (on `QuerysetProxy`)
        when one of the keyword arguments should be the through model name with a dict of values
    * you can order by on through model fields
    * you can filter on through model fields
    * you can include and exclude fields on through models
    * through models are attached only to related models (i.e. if you query from A to B -> only on B)
    * note that through models are explicitly loaded without relations -> relation is already populated in ManyToMany field. 
    * note that just like before you cannot declare the relation fields on through model, they will be populated for you by `ormar`,
      but now if you try to do so `ModelDefinitionError` will be thrown
    * check the updated ManyToMany relation docs for more information

# Other
* Updated docs and api docs
* Refactors and optimisations mainly related to filters, exclusions and order bys


# 0.9.5

## Fixes
* Fix creation of `pydantic` FieldInfo after update of `pydantic` to version >=1.8
* Pin required dependency versions to avoid such situations in the future


# 0.9.4

## Fixes
* Fix `fastapi` OpenAPI schema generation for automatic docs when multiple models refer to the same related one


# 0.9.3

## Fixes
* Fix `JSON` field being double escaped when setting value after initialization
* Fix `JSON` field not respecting `nullable` field setting due to `pydantic` internals 
* Fix `choices` verification for `JSON` field
* Fix `choices` not being verified when setting the attribute after initialization
* Fix `choices` not being verified during `update` call from `QuerySet`


# 0.9.2

## Other
* Updated the Quick Start in docs/readme
* Updated docs with links to queries subpage
* Added badges for code climate and pepy downloads


# 0.9.1

## Features
* Add choices values to `OpenAPI` specs, so it looks like native `Enum` field in the result schema.

## Fixes
* Fix `choices` behavior with `fastapi` usage when special fields can be not initialized yet but passed as strings etc.

# 0.9.0

## Important
* **Braking Fix:** Version 0.8.0 introduced a bug that prevents generation of foreign_keys constraint in the database,
both in alembic and during creation through sqlalchemy.engine, this is fixed now.
* **THEREFORE IF YOU USE VERSION >=0.8.0 YOU ARE STRONGLY ADVISED TO UPDATE** cause despite
that most of the `ormar` functions are working your database **CREATED with ormar (or ormar + alembic)** 
  does not have relations and suffer from perspective of performance and data integrity.
* If you were using `ormar` to connect to existing database your performance and integrity 
  should be fine nevertheless you should update to reflect all future schema updates in your models.


## Breaking
* **Breaking:** All foreign_keys and unique constraints now have a name so `alembic` 
  can identify them in db and not depend on db
* **Breaking:** During model construction if `Meta` class of the `Model` does not 
  include `metadata` or `database` now `ModelDefinitionError` will be raised instead of generic `AttributeError`.
* **Breaking:** `encode/databases` used for running the queries does not have a connection pool
for sqlite backend, meaning that each querry is run with a new connection and there is no way to 
  enable enforcing ForeignKeys constraints as those are by default turned off on every connection.
  This is changed in `ormar` since >=0.9.0 and by default each sqlite3 query has `"PRAGMA foreign_keys=1;"`
  run so now each sqlite3 connection by default enforces ForeignKey constraints including cascades.

## Other

* Update api docs.
* Add tests for fk creation in db and for cascades in db

# 0.8.1

## Features

* Introduce processing of `ForwardRef` in relations. 
  Now you can create self-referencing models - both `ForeignKey` and `ManyToMany` relations. 
  `ForwardRef` can be used both for `to` and `through` `Models`.
* Introduce the possibility to perform two **same relation** joins in one query, so to process complex relations like:
  ```
      B = X = Y
    //
   A 
    \
      C = X = Y <= before you could link from X to Y only once in one query
                   unless two different relation were used 
                   (two relation fields with different names)
  ```
* Introduce the `paginate` method that allows to limit/offset by `page` and `page_size`. 
  Available for `QuerySet` and `QuerysetProxy`.

## Other

* Refactoring and performance optimization in queries and joins.
* Add python 3.9 to tests and pypi setup.
* Update API docs and docs -> i.e. split of queries documentation.

# 0.8.0

## Breaking
* **Breaking:** `remove()` parent from child side in reverse ForeignKey relation now requires passing a relation `name`,
as the same model can be registered multiple times and `ormar` needs to know from which relation on the parent you want to remove the child.
* **Breaking:** applying `limit` and `offset` with `select_related` is by default applied only on the main table before the join -> meaning that not the total
  number of rows is limited but just number of main models (first one in the query, the one used to construct it). You can still limit all rows from db response with `limit_raw_sql=True` flag on either `limit` or `offset` (or both)
* **Breaking:** issuing `first()` now fetches the first row ordered by the primary key asc (so first one inserted (can be different for non number primary keys - i.e. alphabetical order of string))
* **Breaking:** issuing `get()` **without any filters** now fetches the first row ordered by the primary key desc (so should be last one inserted (can be different for non number primary keys - i.e. alphabetical order of string))
* **Breaking (internal):** sqlalchemy columns kept at `Meta.columns` are no longer bind to table, so you cannot get the column straight from there

## Features
* Introduce **inheritance**. For now two types of inheritance are possible:
    * **Mixins** - don't subclass `ormar.Model`, just define fields that are later used on different models (like `created_date` and `updated_date` on each child model), only actual models create tables, but those fields from mixins are added
    * **Concrete table inheritance** - means that parent is marked as `abstract=True` in Meta class and each child has its own table with columns from the parent and own child columns, kind of similar to Mixins but parent also is a (an abstract) Model
    * To read more check the docs on models -> inheritance section.
* QuerySet `first()` can be used with `prefetch_related`

## Fixes
* Fix minor bug in `order_by` for primary model order bys
* Fix in `prefetch_query` for multiple related_names for the same model.
* Fix using same `related_name` on different models leading to the same related `Model` overwriting each other, now `ModelDefinitionError` is raised and you need to change the name. 
* Fix `order_by` overwriting conditions when multiple joins to the same table applied.

## Docs
* Split and cleanup in docs:
    *  Divide models section into subsections
    *  Divide relations section into subsections
    *  Divide fields section into subsections
* Add model inheritance section
* Add API (BETA) documentation

# 0.7.5

* Fix for wrong relation column name in many_to_many relation joins (fix [#73][#73])

# 0.7.4

* Allow multiple relations to the same related model/table.
* Fix for wrong relation column used in many_to_many relation joins (fix [#73][#73])
* Fix for wrong relation population for m2m relations when also fk relation present for same model.
* Add check if user provide related_name if there are multiple relations to same table on one model.
* More eager cleaning of the dead weak proxy models.

# 0.7.3

* Fix for setting fetching related model with UUDI pk, which is a string in raw (fix [#71][#71])

# 0.7.2

* Fix for overwriting related models with pk only in `Model.update() with fields passed as parameters` (fix [#70][#70])

# 0.7.1

* Fix for overwriting related models with pk only in `Model.save()` (fix [#68][#68])

# 0.7.0

*  **Breaking:** QuerySet `bulk_update` method now raises `ModelPersistenceError` for unsaved models passed instead of `QueryDefinitionError`
*  **Breaking:** Model initialization with unknown field name now raises `ModelError` instead of `KeyError`
*  Added **Signals**, with pre-defined list signals and decorators: `post_delete`, `post_save`, `post_update`, `pre_delete`, 
`pre_save`, `pre_update`
*  Add `py.typed` and modify `setup.py` for mypy support 
*  Performance optimization
*  Updated docs

# 0.6.2

*  Performance optimization
*  Fix for bug with `pydantic_only` fields being required
*  Add `property_field` decorator that registers a function as a property that will 
   be included in `Model.dict()` and in `fastapi` response
*  Update docs

# 0.6.1

* Explicitly set None to excluded nullable fields to avoid pydantic setting a default value (fix [#60][#60]). 

# 0.6.0

*  **Breaking:** calling instance.load() when the instance row was deleted from db now raises `NoMatch` instead of `ValueError`
*  **Breaking:** calling add and remove on ReverseForeignKey relation now updates the child model in db setting/removing fk column
*  **Breaking:** ReverseForeignKey relation now exposes QuerySetProxy API like ManyToMany relation
*  **Breaking:** querying related models from ManyToMany cleans list of related models loaded on parent model:
    *  Example: `post.categories.first()` will set post.categories to list of 1 related model -> the one returned by first()
    *  Example 2: if post has 4 categories so `len(post.categories) == 4` calling `post.categories.limit(2).all()` -> will load only 2 children and now `assert len(post.categories) == 2`
*  Added `get_or_create`, `update_or_create`, `fields`, `exclude_fields`, `exclude`, `prefetch_related` and `order_by` to QuerySetProxy 
so now you can use those methods directly from relation  
*  Update docs

# 0.5.5

*  Fix for alembic autogenaration of migration `UUID` columns. It should just produce sqlalchemy `CHAR(32)` or `CHAR(36)`
*  In order for this to work you have to set user_module_prefix='sa.' (must be equal to sqlalchemy_module_prefix option (default 'sa.'))

# 0.5.4

*  Allow to pass `uuid_format` (allowed 'hex'(default) or 'string') to `UUID` field to change the format in which it's saved.
   By default field is saved in hex format (trimmed to 32 chars (without dashes)), but you can pass 
   format='string' to use 36 (with dashes) instead to adjust to existing db or other libraries.
   
   Sample:
   *  hex value = c616ab438cce49dbbf4380d109251dce
   *  string value = c616ab43-8cce-49db-bf43-80d109251dce

# 0.5.3

*  Fixed bug in `Model.dict()` method that was ignoring exclude parameter and not include dictionary argument.

# 0.5.2

*  Added `prefetch_related` method to load subsequent models in separate queries.
*  Update docs

# 0.5.1

* Switched to github actions instead of travis
* Update badges in the docs

# 0.5.0

* Added save status -> you can check if model is saved with `ModelInstance.saved` property
    *  Model is saved after `save/update/load/upsert` method on model
    *  Model is saved after `create/get/first/all/get_or_create/update_or_create` method
    *  Model is saved when passed to `bulk_update` and `bulk_create`
    *  Model is saved after adding/removing `ManyToMany` related objects (through model instance auto saved/deleted)
    *  Model is **not** saved after change of any own field (including pk as `Model.pk` alias)
    *  Model is **not** saved after adding/removing `ForeignKey` related object (fk column not saved)
    *  Model is **not** saved after instantation with `__init__` (w/o `QuerySet.create` or before calling `save`)
*  Added `Model.upsert(**kwargs)` that performs `save()` if pk not set otherwise `update(**kwargs)`
*  Added `Model.save_related(follow=False)` that iterates all related objects in all relations and checks if they are saved. If not it calls `upsert()` on each of them.
*  **Breaking:** added raising exceptions if `add`-ing/`remove`-ing not saved (pk is None) models to `ManyToMany` relation
*  Allow passing dictionaries and sets to fields and exclude_fields
*  Auto translate str and lists to dicts for fields and exclude_fields
*  **Breaking:** passing nested models to fields and exclude_fields is now by related ForeignKey name and not by target model name 
*  Performance optimizations - in modelproxy, newbasemodel - > less queries, some properties are cached on models
*  Cleanup of unused relations code
*  Optional performance dependency orjson added (**strongly recommended**)
*  Updated docs

# 0.4.4

*  add exclude_fields() method to exclude fields from sql
*  refactor column names setting (aliases)
*  fix ordering by for column with aliases
*  additional tests for fields and exclude_fields
*  update docs

# 0.4.3

*  include properties in models.dict() and model.json()

# 0.4.2

*  modify creation of pydantic models to allow returning related models with only pk populated

# 0.4.1

*  add order_by method to queryset to allow sorting
*  update docs

# 0.4.0

*  Changed notation in Model definition -> now use name = ormar.Field() not name: ormar.Field()
    * Note that old notation is still supported but deprecated and will not play nice with static checkers like mypy and pydantic pycharm plugin
*  Type hint docs and test
*  Use mypy for tests also not, only ormar package
*  Fix scale and precision translation with max_digits and decimal_places pydantic Decimal field
*  Update docs - add best practices for dependencies
*  Refactor metaclass and model_fields to play nice with type hints
*  Add mypy and pydantic plugin to docs 
*  Expand the docs on ManyToMany relation

# 0.3.11

* Fix setting server_default as default field value in python

# 0.3.10

* Fix postgresql check to avoid exceptions with drivers not installed if using different backend

# 0.3.9

*  Fix json schema generation as of [#19][#19]
*  Fix for not initialized ManyToMany relations in fastapi copies of ormar.Models
*  Update docs in regard of fastapi use
*  Add tests to verify fastapi/docs proper generation

# 0.3.8

*  Added possibility to provide alternative database column names with name parameter to all fields.
*  Fix bug with selecting related ManyToMany fields with `fields()` if they are empty.
*  Updated documentation

# 0.3.7

*  Publish documentation and update readme

# 0.3.6

*  Add fields() method to limit the selected columns from database - only nullable columns can be excluded.
*  Added UniqueColumns and constraints list in model Meta to build unique constraints on list of columns.
*  Added UUID field type based on Char(32) column type.

# 0.3.5

*  Added bulk_create and bulk_update for operations on multiple objects.

# 0.3.4

Add queryset level methods
*  delete
*  update
*  get_or_create
*  update_or_create

# 0.3.3

*  Add additional filters - startswith and endswith

# 0.3.2

*  Add choices parameter to all fields - limiting the accepted values to ones provided

# 0.3.1

*  Added exclude to filter where not conditions.
*  Added tests for mysql and postgres with fixes for postgres.
*  Rafactors and cleanup.

# 0.3.0

* Added ManyToMany field and support for many to many relations


[#19]: https://github.com/collerek/ormar/issues/19
[#60]: https://github.com/collerek/ormar/issues/60
[#68]: https://github.com/collerek/ormar/issues/68
[#70]: https://github.com/collerek/ormar/issues/70
[#71]: https://github.com/collerek/ormar/issues/71
[#73]: https://github.com/collerek/ormar/issues/73
