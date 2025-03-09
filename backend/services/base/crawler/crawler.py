from abc import abstractmethod
from typing import Generic, List, Optional, Generic, cast

from bs4 import BeautifulSoup

from mixins.http_client import HTTPMetaclass
from .scrape import scrape_async
from services.base.dto import DTO

from aiohttp import ClientSession


class ParseHTMLException(Exception):

    def __init__(self, message: str, errors=[]):
        super().__init__(message)
        self.errors = errors


class BaseCrawler(Generic[DTO], metaclass=HTTPMetaclass):

    async def scrape_detail_async(
        self, urls: List[str], session: Optional[ClientSession] = None, **kwargs
    ) -> List[DTO]:
        if session is None:
            raise ValueError("parameter 'session' cannot be None.")

        return await self._scrape_detail_async(urls, session=session, **kwargs)

    async def _scrape_detail_async(self, urls: List[str], session: ClientSession,
                                   **kwargs) -> List[DTO]:

        dtos = await scrape_async(
            url=urls,
            session=session,
            post_process=self._parse_detail,
        )

        dtos_: List[DTO] = []
        errors: List[Exception] = []
        for dto in dtos:
            if isinstance(dto, BaseException):
                errors.append(dto)
                continue
            dtos_.append(dto)

        if len(errors) > 0:
            raise ExceptionGroup("크롤링 중 오류가 발생했습니다.", errors)

        return [cast(DTO, {**dto, "url": url}) for dto, url in zip(dtos_, urls)]

    @abstractmethod
    def _parse_detail(self, soup: BeautifulSoup) -> DTO | ParseHTMLException:
        pass
