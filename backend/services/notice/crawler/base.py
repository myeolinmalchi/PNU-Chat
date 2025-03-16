from abc import abstractmethod
import asyncio
from datetime import date
from typing import Callable, Generic, List, Optional, Tuple

from aiohttp import ClientSession
from bs4 import Tag
from services.base.crawler import preprocess, scrape
from services.base.crawler.crawler import BaseCrawler, ParseHTMLException
from services.base.service import BaseCrawlerService
from services.base.types.calendar import SemesterType
from services.notice.base import NoticeModelT
from services.notice.dto import NoticeDTO


class BaseNoticeCrawler(BaseCrawler[NoticeDTO]):

    async def parse_documents_async(
        self,
        dtos: List[NoticeDTO],
        session: Optional[ClientSession] = None,
    ):
        """첨부파일(.hwp, .pptx, .ppt, .pdf) 파싱"""

        if not session:
            raise ValueError("'session' must be provided")

        parsed_content_future = [
            scrape.parse_document_async(
                [att["url"] for att in dto["attachments"]],
                session,
            ) for dto in dtos
        ]

        parsed_content = await asyncio.gather(*parsed_content_future)

        attachment_dtos = [[{
            "name": att["name"],
            "url": att["url"],
            "content": [str(preprocess.clean_html(content).prettify()) for content in list(ps.values())]
        } for ps, att in zip(pss, dto["attachments"])] for pss, dto in zip(parsed_content, dtos)]

        dtos = [NoticeDTO(**{**dto, "attachments": att}) for dto, att, in zip(dtos, attachment_dtos)]

        return dtos

    @abstractmethod
    async def scrape_important_urls_async(self, **kwargs) -> List[str]:
        """공지 리스트에서 중요 공지 게시글 url 추출"""
        pass

    @abstractmethod
    async def scrape_urls_async(self, **kwargs) -> List[str]:
        """공지 리스트에서 각 게시글 url 추출"""
        pass

    @abstractmethod
    def _parse_paths_from_table_element(
        self,
        table_element: Tag,
        **kwargs,
    ) -> ParseHTMLException | List[Tuple[str, date]]:
        """table 태그에서 모든 게시글 경로 추출"""
        pass

    @abstractmethod
    def _validate_detail_path(self, path: str, **kwargs) -> bool:
        """게시글 상세페이지 url 검증"""
        pass

    async def fetch_paths_async(
        self,
        index_url: str,
        batch_size: int,
        filter: Callable[[str, date], bool],
        delay_range: Tuple[float, float] = (1, 2),
        session: Optional[ClientSession] = None,
        **kwargs
    ) -> List[str]:
        """전체 게시글 경로 추출"""

        if not session:
            raise ValueError("'session' must be provided")

        rows: int = kwargs.get("rows", 500)

        total_paths: List[str] = []
        st, ed = 0, batch_size

        while True:
            urls = [f"{index_url}?row={rows}&page={page + 1}" for page in range(st, ed)]

            results_with_error = await scrape.scrape_async(
                url=urls,
                session=session,
                post_process=self._parse_paths_from_table_element,
                delay_range=delay_range,
            )

            results: List[Tuple[str, date]] = []
            errors: List[Exception] = []
            for result in results_with_error:
                if isinstance(result, BaseException):
                    errors.append(result)
                    continue

                results += result

            if len(errors) > 0:
                raise ExceptionGroup("크롤링 중 오류가 발생했습니다.", errors)

            paths = [path for path, _date in results if filter(path, _date)]
            total_paths += paths

            if len(paths) < len(urls):
                break

            st, ed = st + batch_size, ed + batch_size

        return total_paths


class BaseNoticeCrawlerService(
    BaseCrawlerService[NoticeDTO, NoticeModelT],
    Generic[NoticeModelT],
):

    @abstractmethod
    def add_semester_info(
        self,
        semesters: List[SemesterType],
        batch_size: int = 500,
    ) -> int:
        pass
