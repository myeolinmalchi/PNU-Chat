from typing import List, Literal, Optional
from dependency_injector.wiring import Provide
from containers.notice import NoticeContainer
from services.base.types.calendar import SemesterType
from services.notice.search.department import IDepartmentNoticeSearchService

from langchain_core.tools import tool


def init_department_tools(notice_service: IDepartmentNoticeSearchService = Provide[NoticeContainer.notice_service]):

    @tool
    async def search_notices(
        query: str,
        departments: List[str],
    ):
        """학과별 공지사항 게시판에서 관련 공지를 검색합니다.

        Parameters:
            - query: 문맥 검색에 사용되는 쿼리. 문장 형태로 작성합니다.
        """

        notices = await notice_service.search_notices_async(query, departments=departments)
        contexts = [notice_service.dto2context(notice) for notice in notices]

        return contexts

    @tool
    async def get_basic_info(departments: List[str]):
        """학과의 기본적인 정보를 불러옵니다.

        Parameters:
            - departments: 검색할 학과 배열
        """

        return ""

    @tool
    async def get_major_courses(
        departments: List[str],
        cohort: Optional[int] = None,
        grades: Optional[List[Literal[1, 2, 3, 4]]] = None,
        terms: Optional[List[Literal[1, 2]]] = None,
        is_required: Optional[bool] = None,
    ):
        """학과의 전공 교과목을 불러옵니다.

        Parameters:
            - departments: 학과 배열
            - cohort: 입학년도(교육과정)
            - grades: 교육과정상의 수강 학년
            - terms: 교육과정상의 수강 학기
            - is_required: 전공 필수 여부 (null일 경우 무관)
        """

        return ""

    @tool
    async def get_graduation_requirements(
        department: str,
        cohort: int,
    ):
        """ 졸업 규정을 불러옵니다.
        
        Parameters:
            - department: 학과 선택
            - cohort: 입학년도 (교육과정)
        """

        return ""

    @tool
    async def get_lectures(
        departments: List[str],
        cohort: Optional[int] = None,
        grades: Optional[List[Literal[1, 2, 3, 4]]] = None,
        terms: Optional[List[Literal[1, 2]]] = None,
        professors: Optional[List[str]] = None,
        is_required: Optional[bool] = None,
        semester: Optional[SemesterType] = None,
    ):
        """학과에서 개설한 수업을 불러옵니다.

        Parameters:
            - departments: 학과 배열
            - cohort: 입학년도 (교육과정)
            - grades: 교육과정상의 수강 학년
            - terms: 교육과정상의 수강 학기
            - professors: 수업 담당 교수님 목록
            - is_required: 전공 필수 여부 (null일 경우 무관)
            - semester: 검색 년도 및 학기 (year: 년도, _type: 겨울방학(1~2월), 1학기(3~6월), 여름방학(7~8월), 2학기(9~12월))
        """

        return ""

    return [
        search_notices,
        get_basic_info,
        get_major_courses,
        get_graduation_requirements,
        get_lectures,
    ]
