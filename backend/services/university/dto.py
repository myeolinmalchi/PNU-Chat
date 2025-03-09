from typing import List, NotRequired, Required
from services.base.dto import BaseDTO
from services.base.types.calendar import DateRangeType, SemesterType
from services.professor.dto import ProfessorInfoDTO


class CalendarDTO(BaseDTO):
    semester: SemesterType
    date_range: DateRangeType
    description: str


class DepartmentDTO(BaseDTO, total=False):
    name: Required[str]
    major: NotRequired[List[str]]
    professors: NotRequired[List[ProfessorInfoDTO]]
    #notices: Optional[List[NoticeDTO]]


class UniversityDTO(BaseDTO):
    name: Required[str]
    departments: NotRequired[List[DepartmentDTO]]
