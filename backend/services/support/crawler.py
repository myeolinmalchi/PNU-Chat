import asyncio
from typing import List, Optional
from aiohttp import ClientSession
from bs4 import Tag
from bs4.element import NavigableString
from services.base.crawler.crawler import BaseCrawler

from services.base.crawler.scrape import parse_document_async
from services.support.dto import SupportDTO
from services.base.crawler import preprocess

DOMAIN = "https://onestop.pusan.ac.kr"


class SupportCrawler(BaseCrawler[SupportDTO]):

    async def parse_documents_async(
        self,
        dtos: List[SupportDTO],
        session: Optional[ClientSession] = None,
    ):
        if not session:
            raise ValueError("'session' must be provided")

        parsed_content_future = [
            parse_document_async(
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

        dtos = [SupportDTO(**{**dto, "attachments": att}) for dto, att, in zip(dtos, attachment_dtos)]

        return dtos

    def _parse_detail(self, soup):
        """학지시 상세 내용 파싱"""

        pages = soup.select(".tab-content > .tab-pane")

        attachments = []
        content: List[str] = []

        nav_elements = soup.select(".nav-item")

        for idx, page in enumerate(pages):

            message_section = page.find("message-box message-body", recursive=False)
            file_section = soup.find(class_="file_tabs2")
            content_section = page.select_one(".sec-2")

            if not content_section:
                continue

            if isinstance(message_section, Tag):
                message_section.extract()
                content_section.insert(0, message_section)

            if len(nav_elements) > idx:
                nav_element = nav_elements[idx]
                heading_text = nav_element.get_text(strip=True)
                heading_element = soup.new_tag(name="h2", string=heading_text)
                content_section.insert(0, heading_element)

            if isinstance(file_section, Tag):
                for e in file_section.select(".my-2"):
                    anchor = e.select("a")[-1]
                    if not anchor.has_attr("href"):
                        continue

                    name_element = next(e.children)
                    if not isinstance(name_element, NavigableString):
                        continue

                    name = name_element.string
                    if len(nav_elements) > idx:
                        heading_text = nav_elements[idx].get_text(strip=True)
                        name = f"{heading_text}_{name}"

                    attachments.append({
                        "name": name,
                        "url": f"{DOMAIN}{anchor['href']}",
                    })

                    e.extract()
                    name_element.extract()

            content_str = str(preprocess.clean_html(content_section).prettify())
            content.append(content_str)

        for e in soup.select(".my-2"):
            anchor = e.select("a")[-1]
            if not anchor.has_attr("href"):
                continue

            name_element = next(e.children)
            if not isinstance(name_element, NavigableString):
                continue

            attachments.append({
                "name": name_element.string,
                "url": f"{DOMAIN}{anchor['href']}",
            })

            e.extract()
            name_element.extract()

        dto = {"info": {"content": content}, "attachments": attachments}
        return SupportDTO(**dto)
