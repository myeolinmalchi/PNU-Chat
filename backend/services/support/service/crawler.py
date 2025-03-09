from typing import Dict, List, Union
from db.models.support import SupportModel
from services.base.service import BaseCrawlerService
from services.support.dto import SupportDTO
from services.support.service.base import BaseSupportService
import json
from config.logger import _logger
import asyncio

from tqdm import tqdm

logger = _logger(__name__)


class SupportCrawlerService(
    BaseSupportService,
    BaseCrawlerService[SupportDTO, SupportModel],
):

    URLDictType = Dict[str, Union[str, "URLDictType"]]

    def _dict2dtos(self, url_dict: URLDictType):
        from itertools import chain

        def help(
            key: str,
            value: str | dict,
            parents: List[str],
            acc: List[SupportDTO],
        ) -> List[SupportDTO]:
            match (value, parents):
                case (str(url), []):
                    info = {"category": key, "sub_category": key, "title": key}
                    return [*acc, SupportDTO(**{"info": info, "url": url})]
                case (str(url), [category]):
                    info = {"category": category, "sub_category": key, "title": key}
                    return [*acc, SupportDTO(**{"info": info, "url": url})]
                case (str(url), [category, sub_category]):
                    info = {"category": category, "sub_category": sub_category, "title": key}
                    return [*acc, SupportDTO(**{"info": info, "url": url})]
                case (dict(), _):
                    result = [help(k, v, [*parents, key], acc) for k, v in value.items()]
                    return list(chain(*result))
                case _:
                    return []

        result = [help(k, v, [], []) for k, v in url_dict.items()]
        return list(chain(*result))

    async def run_crawling_pipeline(self, **kwargs):

        with open("config/onestop.json", "r") as f:
            url_dict = json.load(f)

        dtos = self._dict2dtos(url_dict)

        if kwargs.get("reset", False):
            affected = self.support_repo.delete_all()
            logger(f"{affected} rows affected")

        interval = kwargs.get('interval', 30)
        models = []

        def merge_dto(d1: SupportDTO, d2: SupportDTO):
            info1, info2 = d1["info"], d2["info"]
            info = {**info1, "content": info2["content"]}
            attachments = d2["attachments"] if "attachments" in d2 else []
            return SupportDTO(**{
                "info": info,
                "attachments": attachments,
                "url": d1["url"],
            })

        try:
            pbar = tqdm(range(0, len(dtos), interval), total=len(dtos))

            total_document_pages = 0

            for st in pbar:
                ed = min(st + interval, len(dtos))
                pbar.set_postfix({'range': f"{st + 1} ~ {ed}"})

                urls_batch = [dto["url"] for dto in dtos[st:ed]]

                pbar.set_description("상세페이지 크롤링")
                supports = await self.support_crawler.scrape_detail_async(urls_batch)
                supports = list(map(merge_dto, dtos[st:ed], supports))

                pbar.set_description("첨부파일 파싱")
                supports = await self.support_crawler.parse_documents_async(supports)

                curr_pages = sum([
                    sum([len(att["content"]) for att in dto["attachments"] if "content" in att]) for dto in supports
                    if "attachments" in dto
                ])
                total_document_pages += curr_pages

                pbar.set_description("임베딩")
                supports = await self.support_embedder.embed_dtos_async(dtos=supports)

                support_models = [self.dto2orm(n) for n in supports]
                support_models = [n for n in support_models if n]
                support_models = self.support_repo.create_all(support_models)

                models += support_models

                pbar.update(interval)

                await asyncio.sleep(kwargs.get('delay', 0))

            logger(f"total pages: {total_document_pages}")

        except TimeoutError as e:
            logger(f"크롤링에 실패하였습니다.")
            logger(f"{e}")

        return [self.orm2dto(orm) for orm in models]
