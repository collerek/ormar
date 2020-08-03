class AsyncOrmException(Exception):
    pass


class ModelDefinitionError(AsyncOrmException):
    pass


class ModelNotSet(AsyncOrmException):
    pass


class MultipleResults(AsyncOrmException):
    pass


class RelationshipNotFound(AsyncOrmException):
    pass
