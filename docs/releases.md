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