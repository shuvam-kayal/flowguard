from typing import Any


def get_value(obj: Any, key: str, default=None):
    """Read a field from either dict-like or Pydantic/object input."""
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)