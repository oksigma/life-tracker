class NotFoundError(Exception):
    """Raised when a requested resource does not exist. Converted to a 404 response."""

    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} not found")
        self.resource = resource
