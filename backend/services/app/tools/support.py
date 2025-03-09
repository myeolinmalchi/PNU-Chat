from openai.types.shared_params import FunctionDefinition
from functools import lru_cache


def create_tool_search_supports():
    return FunctionDefinition(
        name="search_supports",
        description=(
            "학생지원시스템에서 학교 생활 전반(기숙사, 동아리, 장학금, 행정 업무 등)에 대한 정보를 검색합니다. "
            "특정한 분야(예: 학사일정, 수업정보)로 분류하기 애매하거나, 잘 모르겠는 질문이라면 우선 이 함수를 사용하세요.\n\n"
            "예시:\n"
            "  - '현장실습은 몇학년부터 가능한가요?'\n"
            "  - '장학금 신청 자격 조건이 궁금해요.'\n"
            "  - '기숙사에 있는 편의시설 목록 알려주세요.'\n"
            "  - '학생회관 이용 시간과 위치가 궁금합니다.'\n"
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "사용자의 질문에 포함된 키워드를 확장하여 더 넓은 의미의 질문을 생성합니다. 반드시 의문문이어야 합니다. 질문에 포함된 키워드의 유사어, 상위어 사용하여 검색 범위를 확장합니다. 매우 상세하고 구체적인 질문이어야 합니다."
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        strict=True
    )
