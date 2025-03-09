from openai.types.shared_params import FunctionDefinition
from functools import lru_cache

from db.models.calendar import SemesterTypeEnum
from services.app.tools.common import create_tool_param_semesters


def create_tool_search_notice(
    academic_year: int,
    semester_type: SemesterTypeEnum,
    departments_str: str,
):
    params = {
        """
        **(create_tool_param_semesters(
            academic_year,
            semester_type,
        )),
        """
        "query": {
            "type": "string",
            "description": "사용자의 질문에 사용된 키워드를 확장하여 더 넓은 의미의 질문을 생성합니다. 반드시 의문문이어야 합니다. 질문에 포함된 키워드의 유사어, 상위어 사용하여 검색 범위를 확장합니다. (ex: 개강 날짜는 언제인가요?)"
        },
        "departments": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": departments_str.split(","),
                "description": "검색할 학과를 결정합니다. 사용자가 특정 학과를 언급하지 않는다면 학생의 학과를 포함하세요. 최소 한 개 이상의 학과를 포함하세요."
            }
        },
        "additionalProperties": False,
    }

    return FunctionDefinition(
        name="search_notices",
        description="**학과 공지사항**에서 수업, 학과 생활, 공모전 등의 정보를 검색합니다.",
        parameters={
            "type": "object",
            "properties": params,
            "required": ["query", "departments"],
            "strict": True,
        },
    )
