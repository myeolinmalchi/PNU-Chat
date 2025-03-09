from abc import abstractmethod
import asyncio
from typing import List, Optional

from aiohttp import ClientSession
from services.base.crawler import preprocess, scrape
from services.base.crawler.crawler import BaseCrawler
from services.notice.dto import NoticeDTO


class BaseNoticeCrawler(BaseCrawler[NoticeDTO]):

    async def parse_documents_async(
        self,
        dtos: List[NoticeDTO],
        session: Optional[ClientSession] = None,
    ):
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
    async def scrape_urls_async(self, **kwargs) -> List[str]:
        """공지 리스트에서 각 게시글 url 추출"""
        pass
