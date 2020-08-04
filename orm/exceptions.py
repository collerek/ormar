class AsyncOrmException(Exception):
    pass


class ModelDefinitionError(AsyncOrmException):
    pass


class ModelNotSet(AsyncOrmException):
    pass


class NoMatch(AsyncOrmException):
    pass


class MultipleMatches(AsyncOrmException):
    pass


class RelationshipNotFound(AsyncOrmException):
    pass
