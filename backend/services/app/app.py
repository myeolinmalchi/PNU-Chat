from datetime import datetime
from functools import lru_cache
from typing import NotRequired, Optional, Tuple, TypedDict, Unpack, Required, List

from aiohttp import ClientSession
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall, ChatCompletionToolParam

from app.schemas.chat import SearchHistory
from db.models.calendar import SemesterTypeEnum
from db.repositories.calendar import SemesterRepository

from services.app.tools import create_tool_search_notice, create_tool_search_supports
from services.app.tools.university import create_tool_search_calendar

from services.base.embedder import rerank_async
from services.base.types.calendar import SemesterType
from services.base.service import BaseService

from services import notice, professor, support, university

import json
import asyncio

from config.logger import _logger

logger = _logger(__name__)


class ApplicationService(BaseService):

    def __init__(
        self,
        notice_service: notice.BaseNoticeSearchService,
        professor_service: professor.ProfessorService,
        support_service: support.BaseSupportSearchService,
        calendar_service: university.CalendarService,
        univ_service: university.UniversityService,
        semester_repo: SemesterRepository,
    ):
        self.notice_service = notice_service
        self.professor_service = professor_service
        self.support_service = support_service
        self.calendar_service = calendar_service
        self.univ_service = univ_service
        self.semester_repo = semester_repo

    def load_today_info(self):
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        semester = self.calendar_service.get_semester(year, month, day)
        return now, semester[0]

    @lru_cache
    def load_tools(
        self,
        academic_year: int,
        semester_type: SemesterTypeEnum,
    ):
        from itertools import chain

        department_dict = self.univ_service.search_all_departments()
        department_names = list(chain(*department_dict.values()))

        department_names = [name for name in department_names]
        departments_str = ",".join(department_names)

        tools = [
            create_tool_search_supports(),
            create_tool_search_calendar(academic_year, semester_type),
            create_tool_search_notice(academic_year, semester_type, departments_str),
        ]

        return [ChatCompletionToolParam(type="function", function=tool) for tool in tools]

    async def call_by_name(self, tool_name: str, **args):
        import inspect

        func = getattr(self, tool_name)
        if inspect.iscoroutinefunction(func):
            return await func(**args)
        return func(**args)

    async def call(self, tool_call: ChatCompletionMessageToolCall):
        tool_name: str = tool_call.function.name
        tool_args: dict = json.loads(tool_call.function.arguments)

        logger(f"[{tool_name}] ({tool_args})")
        if not hasattr(self, tool_name):
            return None

        return await self.call_by_name(tool_name, **tool_args)

    async def call_by_chat(
        self,
        completion: ChatCompletion,
    ) -> List[Tuple[List[str], ChatCompletionMessageToolCall]] | str | None:

        tool_calls = completion.choices[0].message.tool_calls
        if not tool_calls:
            return completion.choices[0].message.content

        tool_results = await asyncio.gather(*[self.call(tool_call) for tool_call in tool_calls])
        results = [(tool_result, tool_call) for tool_result, tool_call in zip(tool_results, tool_calls) if tool_result]

        return results

    async def filter_relate_contexts_async(
        self,
        answer: str,
        contexts: List[SearchHistory],
        session: Optional[ClientSession] = None,
        threshold: float = 0.3,
    ) -> List[SearchHistory]:
        if not session:
            raise ValueError("'session' must be provided")

        filtered_contexts = []
        for context in contexts:
            if isinstance(context.content, str):
                ranks = await rerank_async(answer, [context.content], session)
                if ranks[0]["score"] >= threshold:
                    filtered_contexts.append(context)

            if isinstance(context.content, list):
                ranks = await rerank_async(answer, context.content, session)
                filtered_indexes = [rank["index"] for rank in ranks if rank["score"] >= threshold]
                filtered_contents = [context for idx, context in enumerate(context.content) if idx in filtered_indexes]
                if len(filtered_contents) == 0:
                    continue

                context.content = filtered_contents
                filtered_contexts.append(context)

        return filtered_contexts

    class SearchOpts(TypedDict):
        count: NotRequired[int]
        lexical_ratio: NotRequired[float]

    class SearchNoticeOpts(SearchOpts):
        query: str
        semesters: Required[List[SemesterType]]
        departments: Required[List[str]]

    class SearchProfessorOpts(SearchOpts):
        query: str
        departments: Required[List[str]]

    class SearchSupportOpts(SearchOpts):
        query: str

    async def search_notices(self, **opts: Unpack[SearchNoticeOpts]):
        notices = await self.notice_service.search_notices_async(**opts)
        return [self.notice_service.dto2context(notice) for notice in notices]

    def search_calendars(self, semesters: List[SemesterType]):
        calendars = self.calendar_service.search_calendars(semesters)
        return [self.calendar_service.dto2context(dto) for dto in calendars]

    def search_professors(self, **opts: Unpack[SearchNoticeOpts]):
        return self.professor_service.search_professors(**opts)

    async def search_supports(self, **opts: Unpack[SearchSupportOpts]):
        supports = await self.support_service.search_supports_async(**opts)
        return [self.support_service.dto2context(support) for support in supports]
