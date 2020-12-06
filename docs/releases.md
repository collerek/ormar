# 0.7.0

*  **Breaking:** QuerySet `bulk_update` method now raises `ModelPersistenceError` for unsaved models passed instead of `QueryDefinitionError`
*  **Breaking:** Model initialization with unknown field name now raises `ModelError` instead of `KeyError`
*  
*  Add py.typed and modify setup.py for mypy support 
*  Performance optimization

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