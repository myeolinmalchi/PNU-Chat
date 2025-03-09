from functools import lru_cache

from openai.types.shared_params import FunctionDefinition

from db.models.calendar import SemesterTypeEnum
from services.app.tools.common import create_tool_param_semesters


@lru_cache
def create_tool_search_calendar(
    academic_year: int,
    semester_type: SemesterTypeEnum,
):
    params = {
        **(create_tool_param_semesters(
            academic_year,
            semester_type,
        )),
    }

    return FunctionDefinition(
        name="search_calendars",
        description="""\
        "구체적인" 일자를 확인해야 할 때 사용합니다.
        `search_supports`와 함께 사용합니다.
        """,
        parameters={
            "type": "object",
            "properties": params,
            "required": ["semesters"],
            "strict": True
        },
    )
