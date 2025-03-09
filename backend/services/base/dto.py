from typing import Dict, List, NotRequired, Optional, Required, TypedDict, TypeVar
from pydantic import BaseModel, HttpUrl


class BaseDTOV2(BaseModel):
    url: HttpUrl


class BaseDTO(TypedDict, total=False):
    url: Required[str]


DTO = TypeVar("DTO", bound=BaseDTO)


class EmbedResultV2(BaseModel):
    chunk: Optional[str]
    dense: List[float]
    sparse: Dict[int, float]


class EmbedResult(TypedDict):
    chunk: NotRequired[str]
    dense: List[float]
    sparse: Dict[int, float]


class RerankResult(TypedDict):
    index: int
    score: float
