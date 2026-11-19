from bson import ObjectId

from app.core.errors import NotFoundError


def parse_object_id(value: str, resource: str) -> ObjectId:
    """Parse an id from a URL. Invalid ids are treated as "not found" rather than a 400."""
    if not ObjectId.is_valid(value):
        raise NotFoundError(resource)
    return ObjectId(value)
