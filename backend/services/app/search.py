from typing import List, NotRequired, TypedDict, Required, Unpack

from services import notice, professor, support, university, base
from db import repositories

from datetime import datetime
from config.logger import _logger

logger = _logger("AppSearchService")


class AppSearchService(base.BaseService):

    def __init__(
        self,
        notice_service: notice.IDepartmentNoticeSearchService,
        professor_service: professor.ProfessorService,
        support_service: support.BaseSupportSearchService,
        calendar_service: university.CalendarService,
        univ_service: university.UniversityService,
        semester_repo: repositories.SemesterRepository,
        pnu_notice_service: notice.IPNUNoticeSearchService,
    ):
        self.notice_service = notice_service
        self.professor_service = professor_service
        self.support_service = support_service
        self.calendar_service = calendar_service
        self.univ_service = univ_service
        self.semester_repo = semester_repo
        self.pnu_notice_service = pnu_notice_service

    def load_today_info(self):
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        semester = self.calendar_service.get_semester(year, month, day)
        return now, semester[0]

    class SearchOpts(TypedDict):
        count: NotRequired[int]
        lexical_ratio: NotRequired[float]

    class SearchNoticeOpts(SearchOpts):
        query: str
        semesters: NotRequired[List[base.SemesterType]]
        departments: Required[List[str]]

    class SearchPNUNoticeOpts(SearchOpts):
        query: str
        semesters: Required[List[base.SemesterType]]

    class SearchProfessorOpts(SearchOpts):
        query: str
        departments: Required[List[str]]

    class SearchSupportOpts(SearchOpts):
        query: str

    async def search_notices(
        self,
        query: str,
        departments: List[str],
        semesters: List[base.SemesterType] = [],
        **_,
    ):
        logger(f"search query(notice): {query}")
        notices = await self.notice_service.search_notices_async(
            query,
            departments=departments,
            semesters=semesters,
        )
        logger(f"count of notices: {len(notices)}")
        return [self.notice_service.dto2context(notice) for notice in notices]

    async def search_pnu_notices(
        self,
        query: str,
        semesters: List[base.SemesterType] = [],
        **_,
    ):
        logger(f"search query(pnu notice): {query}")
        notices = await self.pnu_notice_service.search_notices_async(
            query,
            semesters=semesters,
        )

        logger(f"count of pnu notices: {len(notices)}")

        return [self.notice_service.dto2context(notice) for notice in notices]

    def search_calendars(self, semesters: List[base.SemesterType], **_):
        calendars = self.calendar_service.search_calendars(semesters)
        return [self.calendar_service.dto2context(dto) for dto in calendars]

    def search_professors(self, **opts: Unpack[SearchNoticeOpts]):
        return self.professor_service.search_professors(**opts)

    async def search_supports(self, query: str, **_):
        logger(f"search query(support): {query}")
        supports = await self.support_service.search_supports_async(query)
        calendars = self.calendar_service.search_calendars([])

        support_contexts = [self.support_service.dto2context(support) for support in supports]
        calendar_contexts = [self.calendar_service.dto2context(dto) for dto in calendars]

        return [*calendar_contexts, *support_contexts]
