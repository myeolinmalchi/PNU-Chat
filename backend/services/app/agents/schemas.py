from enum import Enum
from typing import List
from pydantic import BaseModel

from db.models.calendar import SemesterTypeEnum


class P0_Answer(BaseModel):
    paragraph: str
    urls: List[str]


class P0_ResponseFormat(BaseModel):
    answers: List[P0_Answer]


class P0_1_ResponseFormat(BaseModel):
    sub_questions: List[str]


class P0_2_ToolEnum(Enum):
    search_notices = "search_notices"
    search_supports = "search_supports"
    #search_calendars = "search_calendars"


class P0_2_ResponseFormat(BaseModel):
    tools: List[P0_2_ToolEnum]


class P0_3_Semester(BaseModel):
    year: int
    type_: SemesterTypeEnum


class P0_3_ResponseFormat(BaseModel):
    query: str
    departments: List[str]
    semesters: List[P0_3_Semester]


class P0_4_Document(BaseModel):
    extracted: str
    urls: List[str]


class P0_4_ResponseFormat(BaseModel):
    documents: List[P0_4_Document]
