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
        "semesters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "검색 **학년도**. **년도**와는 다른 개념입니다."
                    },
                    "type_": {
                        "type": "string",
                        "enum": ["1학기", "2학기", "여름방학", "겨울방학"],
                        "description": "공지사항의 작성 시점을 기준으로 필터링 합니다. 대략 3~6월은 1학기, 7~8월은 여름방학, 9~12월은 2학기, 다음 년도 1~2월은 겨울방학입니다."
                    }
                },
                "required": ["year", "semester"],
                "strict": True
            },
            "description": f"검색 학기를 필터링 합니다. 이 값은 비워두세요."
        },
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
