class ServiceError(Exception):
    """Base class for expected application-service failures."""


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass
