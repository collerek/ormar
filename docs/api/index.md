Contains documentation of the `ormar` internal API.

Note that this is a technical part of the documentation intended for `ormar` contributors.

!!!note
    For completeness as of now even the internal and special methods are documented and exposed in API docs.

!!!warning
    The current API docs version is a beta and not all methods are documented, 
    also some of redundant items are included since it was partially auto generated.

!!!danger
    Ormar is still under development, and the **internals can change at any moment**.

    You shouldn't rely even on the "public" methods if they are not documented in the 
    normal part of the docs.

## High level overview

Ormar is divided into packages for maintainability and ease of development.

Below you can find a short description of the structure of the whole project and 
individual packages.

### Models

Contains the actual `ormar.Model` class, which is based on:

*  `ormar.NewBaseModel` which in turns:
    *  inherits from `pydantic.BaseModel`, 
    *  uses `ormar.ModelMetaclass` for all heavy lifting, relations declaration, 
    parsing `ormar` fields, creating `sqlalchemy` columns and tables etc.
        * There is a lot of tasks during class creation so `ormar` is using a lot of 
          `helpers` methods separated by functionality: `pydantic`, `sqlachemy`, 
          `relations` & `models` located in `helpers` submodule.
    *  inherits from `ormar.ModelTableProxy` that combines `Mixins` providing a special
    additional behavior for `ormar.Models`
        * `AliasMixin` - handling of column aliases, which are names changed only in db
        * `ExcludableMixin` - handling excluding and including fields in dict() and database calls
        * `MergeModelMixin` - handling merging Models initialized from raw sql raws into Models that needs to be merged,
          in example parent models in join query that duplicates in raw response.
        * `PrefetchQueryMixin` - handling resolving relations and ids of models to extract during issuing
          subsequent queries in prefetch_related
        * `RelationMixin` - handling resolving relations names, related fields etc.
        * `SavePrepareMixin` - handling converting related models to their pk values, translating ormar field
        names into aliases etc.
          
### Fields

Contains `ormar.BaseField` that is a base for all fields. 

All basic types are declared in `model_fields`, while relation fields are located in:

*  `foreign_key`: `ForeignKey` relation, expanding relations meaning initializing nested models,
    creating dummy models with pk only that skips validation etc.
*  `many_to_many`: `ManyToMany` relation that do not have a lot of logic on its own.

Related to fields is a `@property_field` decorator that is located in `decorators.property_field`.

There is also a special UUID field declaration for `sqlalchemy` that is based on `CHAR` field type.

### Query Set

Package that handles almost all interactions with db (some small parts are in `ormar.Model` and in `ormar.QuerysetProxy`).

Provides a `QuerySet` that is exposed on each Model as `objects` property.

Have a vast number of methods to query, filter, create, update and delete database rows.

*  Actual construction of the queries is delegated to `Query` class
    * which in tern uses `SqlJoin` to construct joins
    * `Clause` to convert `filter` and `exclude` conditions into sql
    * `FilterQuery` to apply filter clauses on query
    * `OrderQuery` to apply order by clauses on query
    * `LimitQuery` to apply limit clause on query
    * `OffsetQuery` to apply offset clause on query
* For prefetch_related the same is done by `PrefetchQuery`
* Common helpers functions are extracted into `utils`

### Relations

Handles registering relations, adding/removing to relations as well as returning the
actual related models instead of relation fields declared on Models.

* Each `ormar.Model` has its own `RelationManager` registered under `_orm` property.
    * `RelationManager` handles `Relations` between two different models
        * In case of reverse relations or m2m relations the `RelationProxy` is used which
        is basically a list with some special methods that keeps a reference to a list of related models
        * Also, for reverse relations and m2m relations `QuerySetProxy` is exposed, that is
        used to query the already pre-filtered related models and handles Through models
          instances for m2m relations, while delegating actual queries to `QuerySet`
* `AliasManager` handles registration of aliases for relations that are used in queries. 
  In order to be able to link multiple times to the same table in one query each link 
  has to have unique alias to properly identify columns and extract proper values. 
  Kind of global registry, aliases are randomly generated, so might differ on each run.
* Common helpers functions are extracted into `utils`

### Signals

Handles sending signals on particular events.

* `SignalEmitter` is registered on each `ormar.Model`, that allows to register any number of 
receiver functions that will be notified on each event.
* For now only combination of (pre, post) (save, update, delete) events are pre populated for user
although it's easy to register user `Signal`s.
* set of decorators is prepared, each corresponding to one of the builtin signals,
that can be used to mark functions/methods that should become receivers, those decorators
are located in `decorators.signals`.
* You can register same function to different `ormar.Models` but each Model has it's own
Emitter that is independednt and issued on events for given Model. 
* Currently, there is no way to register global `Signal` triggered for all models.

### Exceptions

Gathers all exceptions specific to `ormar`.

All `ormar` exceptions inherit from `AsyncOrmException`. 

