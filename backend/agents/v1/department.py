from typing import List, Literal, Optional
from dependency_injector.wiring import Provide
from langgraph.prebuilt import create_react_agent
from containers.notice import NoticeContainer
from services.base.types.calendar import SemesterType
from services.notice.search.department import IDepartmentNoticeSearchService


def init_department_tools(notice_service: IDepartmentNoticeSearchService = Provide[NoticeContainer.notice_service]):

    async def search_notices(
        query: str,
        departments: List[str],
    ):
        """학과별 공지사항 게시판에서 관련 공지를 검색합니다."""
        notices = await notice_service.search_notices_async(query, departments=departments)
        contexts = [notice_service.dto2context(dto) for dto in notices]

        return contexts

    async def get_basic_info(departments: List[str]):
        """학과의 기본적인 정보를 불러옵니다."""
        return [{
            "department": dept,
            "office": "2호관 301호",
            "contact": "02-1234-5678",
            "website": f"https://university.ac.kr/{dept.lower()}"
        } for dept in departments]

    async def get_major_courses(
        departments: List[str],
        cohort: Optional[int] = None,
        grades: Optional[List[Literal[1, 2, 3, 4]]] = None,
        terms: Optional[List[Literal[1, 2]]] = None,
        is_required: Optional[bool] = None,
    ):
        """학과의 전공 교과목을 불러옵니다."""
        return [{
            "department": departments[0],
            "course_name": "자료구조",
            "grade": 2,
            "term": 1,
            "is_required": True,
            "credits": 3
        }, {
            "department": departments[0],
            "course_name": "인공지능개론",
            "grade": 3,
            "term": 2,
            "is_required": False,
            "credits": 3
        }]

    async def get_graduation_requirements(
        department: str,
        cohort: int,
    ):
        """졸업 규정(학점, 어학성적 등)을 가져옵니다."""
        return {
            "department": department,
            "cohort": cohort,
            "required_credits": 130,
            "required_major_credits": 70,
            "required_general_education_credits": 30,
            "thesis_required": True
        }

    async def get_lectures(
        departments: List[str],
        cohort: Optional[int] = None,
        grades: Optional[List[Literal[1, 2, 3, 4]]] = None,
        terms: Optional[List[Literal[1, 2]]] = None,
        professors: Optional[List[str]] = None,
        is_required: Optional[bool] = None,
        semester: Optional[SemesterType] = None,
    ):
        """학과에서 개설한 수업을 불러옵니다."""
        return [{
            "course_id": "CS101",
            "course_name": "프로그래밍 입문",
            "professor": "홍길동",
            "semester": {
                "year": 2025,
                "_type": "1학기"
            },
            "is_required": True,
            "credits": 3
        }, {
            "course_id": "CS405",
            "course_name": "딥러닝",
            "professor": "김영희",
            "semester": {
                "year": 2025,
                "_type": "2학기"
            },
            "is_required": False,
            "credits": 3
        }]

    return [
        search_notices,
        get_basic_info,
        get_major_courses,
        get_graduation_requirements,
        get_lectures,
    ]


def init_department_agent():
    tools = init_department_tools()
    agent = create_react_agent(
        model="openai:gpt-4.1-nano",
        tools=tools,
        prompt=(""),
        name="department_agent",
    )

    return agent
