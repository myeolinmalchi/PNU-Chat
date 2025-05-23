from functools import lru_cache
from db.models.calendar import SemesterTypeEnum


@lru_cache
def create_tool_param_semesters(
    academic_year: int,
    semester_type: SemesterTypeEnum,
):
    """
    return {
        "semester": {
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
        "description": f"검색 학기를 필터링 합니다."
    }
    """
    return {
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
