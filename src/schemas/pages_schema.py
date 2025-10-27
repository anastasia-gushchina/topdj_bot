from typing import TypeVar
from pydantic import BaseModel, ConfigDict


db_model_type = TypeVar('DBModelType')


class PagesSchema(BaseModel):
    total: int
    data: list[db_model_type]

    def __init__(self, **kwargs):
        db_model_type = kwargs.get("type")
        if db_model_type is None:
            raise ValueError("Missing type of list")
        total = kwargs.get("total")
        data = kwargs.get("data")
        data = [db_model_type(**d) for d in data]

        super().__init__(total=total, data=data)

    model_config = ConfigDict(arbitrary_types_allowed=True)
