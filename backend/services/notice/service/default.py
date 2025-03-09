from typing import List, Tuple
from urllib.parse import urlparse
from tqdm import tqdm
from urllib3.util import parse_url
from config.config import get_notice_urls
from db.models.notice import NoticeModel

import asyncio
from db.repositories.base import transaction
from services.base.service import BaseCrawlerService
from services.base.types.calendar import DateRangeType, SemesterType
from services.notice.crawler.base import BaseNoticeCrawler
from services.notice.dto import NoticeDTO
from services.notice.service.base import BaseNoticeService
from config.logger import _logger

logger = _logger(__name__)


class BaseNoticeCrawlerService(
    BaseNoticeService,
    BaseCrawlerService[NoticeDTO, NoticeModel],
):

    def __init__(self, notice_crawler: BaseNoticeCrawler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notice_crawler = notice_crawler

    def add_semester_info(
        self,
        semesters: List[SemesterType],
        department: str,
        batch_size: int = 500,
    ):

        if not self.semester_repo:
            raise ValueError("'semester_repo' not provided")

        with transaction():
            semester_models = self.semester_repo.search_semesters(semesters)
            assert isinstance(semester_models, list)

        affected = 0
        for semester_model in semester_models:
            st, ed = semester_model.st_date, semester_model.ed_date
            date_range = DateRangeType(st_date=st, ed_date=ed)
            total_records = self.notice_repo.search_total_records(date_ranges=[date_range], departments=[department])

            from tqdm import tqdm
            pbar = tqdm(
                range(0, total_records, batch_size),
                desc=f"학기 정보 추가({semester_model.year}-{semester_model.type_})",
            )
            for offset in pbar:
                notices = self.notice_repo.update_semester(semester_model, batch_size, offset)
                affected += len(notices)

        return affected


class NoticeCrawlerService(BaseNoticeCrawlerService):

    async def run_crawling_batch(
        self,
        urls: List[str],
        department: str,
        category: str,
        base_url: str,
        parse_attachment: bool = False,
    ) -> Tuple[List[NoticeDTO], int]:

        logger("Scrape notices...")
        notices = await self.notice_crawler.scrape_detail_async(urls)
        logger("Done.")

        def add_info(notice: NoticeDTO, **kwargs) -> NoticeDTO:
            for key, value in kwargs.items():
                notice["info"][key] = value

            notice["attachments"] = [{
                "name": att["name"],
                "url": base_url + att["url"] if att["url"].startswith("/") else att["url"]
            } for att in notice["attachments"]]

            return notice

        notices = list(
            map(lambda notice: add_info(
                notice=notice,
                department=department,
                category=category,
            ), notices)
        )

        curr_pages = 0

        if parse_attachment:
            logger("Parse attachments...")
            notices = await self.notice_crawler.parse_documents_async(notices)
            logger("Done.")

            curr_pages = sum([
                sum([len(att["content"]) for att in dto["attachments"] if "content" in att]) for dto in notices
                if "attachments" in dto
            ])

        logger("Embed notices...")
        notices = await self.notice_embedder.embed_dtos_async(dtos=notices)
        logger("Done.")

        notice_models = [self.dto2orm(n) for n in notices]
        notice_models = [n for n in notice_models if n]

        with transaction():
            logger("Create notices...")
            notice_models = self.notice_repo.create_all(notice_models)
            dtos = list(map(self.orm2dto, notice_models))
            logger("Done.")

        return dtos, curr_pages

    async def run_crawling_pipeline(self, **kwargs):
        department = kwargs.get("department")
        if not department:
            raise ValueError("'department' must be provided")

        url_dict = get_notice_urls(department)

        reset = kwargs.get("reset", False)
        interval = kwargs.get('interval', 30)
        rows = kwargs.get('rows', 500)

        if interval > rows:
            interval = rows

        dtos: List[NoticeDTO] = []
        last_year = kwargs.get("last_year", 2000)

        total_pages = 0
        pages_dict = {}

        for category, url in url_dict.items():
            url_instance = urlparse(url)
            base_url = f"{url_instance.scheme}://{url_instance.netloc}"

            search_filter = {
                "departments": [department],
                "categories": [category],
            }

            last_id = None
            if reset:
                affected = self.notice_repo.delete_all(**search_filter)
                logger(f"[{department}-{category}] {affected} rows deleted.")

            else:
                last_notice = self.notice_repo.find_last_notice(**search_filter)
                if last_notice:
                    last_path = parse_url(last_notice.url).path
                    if not last_path:
                        raise ValueError(f"잘못된 url입니다: {last_notice.url}")
                    last_id = int(last_path.split("/")[4])

            urls = await self.notice_crawler.scrape_urls_async(
                url=url,
                rows=rows,
                last_id=last_id,
                last_year=last_year,
            )

            category_pages = 0

            with tqdm(total=len(urls), desc=f"[{department}-{category}]") as pbar:
                for st in range(0, len(urls), interval):
                    ed = min(st + interval, len(urls))
                    pbar.set_postfix({'range': f"{st + 1}-{ed}"})

                    _dtos, pages = await self.run_crawling_batch(
                        urls=urls[st:ed],
                        department=department,
                        category=category,
                        base_url=base_url,
                    )
                    dtos += _dtos
                    category_pages += pages

                    await asyncio.sleep(kwargs.get('delay', 0))

                    pbar.update(len(_dtos))

            total_pages += category_pages
            pages_dict[category] = category_pages
            """
            except Exception:
                logger(f"[{department}-{category}] 크롤링에 실패하여 데이터를 삭제합니다.", level=logging.ERROR)
                affected = self.notice_repo.delete_all(**search_filter)
                logger(f"[{department}-{category}] aff", level=logging.ERROR)

                continue
            """

        return dtos
