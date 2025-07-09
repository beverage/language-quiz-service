import enum

from sqlalchemy import inspect

def object_as_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
    }

class DatabaseStringEnum(enum.Enum):

    def __str__(self):
        return self.name
