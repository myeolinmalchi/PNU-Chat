from datetime import date
from typing import NotRequired, TypedDict

from db.models.calendar import SemesterTypeEnum


class DateRangeType(TypedDict):
    """날짜 범위 타입"""

    st_date: date
    ed_date: date


class SemesterType(TypedDict):
    """학기 타입"""

    semester_id: NotRequired[int]
    year: int
    type_: SemesterTypeEnum
    period: NotRequired[DateRangeType]
