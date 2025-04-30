from typing import List
from pydantic import BaseModel


class EvalQueryItem(BaseModel):
    url: str
    queries: List[str]
