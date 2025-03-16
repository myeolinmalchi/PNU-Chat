"""학과 공지사항 크롤러(기계공학부 제외)"""

import asyncio
from typing import List, Tuple
from urllib.parse import urlparse

from tqdm import tqdm

from config.config import get_notice_urls
from db.models.calendar import SemesterTypeEnum
from db.models.notice import NoticeModel
from db.repositories.base import transaction
from db.repositories.notice import NoticeRepository
from services.base import ParseHTMLException
from services.base.crawler import preprocess, scrape

from urllib3.util import parse_url

from services.base.types.calendar import DateRangeType, SemesterType
from services.notice import NoticeDTO, crawler
from config.logger import _logger
from services.notice.base import BaseDepartmentNoticeService
from services.notice.crawler.base import BaseNoticeCrawlerService
from services.notice.embedder import NoticeEmbedder

SELECTORs = {
    "list": "div._articleTable > form:nth-child(2) table > tbody > tr:not(.headline)",
    "list_important": "div._articleTable > form:nth-child(2) table > tbody > tr.headline",
    "detail": {
        "info": {
            "title": "div.artclViewTitleWrap > h2",
            "content": "div.artclView",
            "author_date": "div.artclViewHead > div.right > dl",
        },
        "attachments": "div.artclItem > dl > dd > ul > li"
    }
}

logger = _logger(__name__)

from datetime import datetime, date


class NoticeCrawler(crawler.BaseNoticeCrawler):

    def _parse_paths_from_table_element(self, table_element, **kwargs):
        table = table_element.select_one("table")

        if not table:
            return ParseHTMLException("<table>이 존재하지 않습니다.")

        is_important = kwargs.get("is_important", False)
        is_common = kwargs.get("is_common", False)

        table_rows = table_element.select(SELECTORs['list_important' if is_important else 'list'])

        results = []
        for row in table_rows:
            anchor = row.select_one("td._artclTdTitle > a")
            if anchor is None or not anchor.has_attr("href"):
                continue

            date = row.select_one("td._artclTdRdate")
            if not date:
                continue

            date_str = date.get_text(strip=True)
            date = datetime.strptime(date_str, "%Y.%m.%d").date()

            href = str(anchor["href"])

            if is_important and is_common and row.select_one("td > span._artclTnotice") is None:
                continue

            if is_important and not is_common and row.select_one("td > span._artclNnotice") is None:
                continue

            results.append((href, date))

        return results

    def _validate_detail_path(self, path, **kwargs) -> bool:
        last_id: int | None = kwargs.get("last_id")
        if last_id is None:
            return True

        ss = path.split('/')[4]
        return int(ss) > int(last_id)

    async def scrape_important_urls_async(self, **kwargs) -> List[str]:
        url = kwargs.get("url")

        if not url:
            raise ValueError("'url' must be provided")

        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        _url = parse_url(url)

        parse_paths = lambda soup: self._parse_paths_from_table_element(
            soup,
            is_important=True,
            is_common=kwargs.get("is_common", False),
        )

        results_with_error = await scrape.scrape_async(
            url=[url],
            session=session,
            post_process=parse_paths,
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

        paths = [path for path, _ in results]

        return [f"{_url.scheme}://{_url.netloc}{path}" for path in paths]

    async def scrape_urls_async(self, **kwargs) -> List[str]:

        url = kwargs.get("url")
        rows = kwargs.get("rows", 500)
        batch_size = kwargs.get("batch_size", 50)

        if not url:
            raise ValueError("'url' must be provided")

        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        _url = parse_url(url)

        last_year = kwargs.get("last_year", date(2000, 1, 1))

        def filter(path: str, _date: date):
            return self._validate_detail_path(path, last_id=last_id) and _date > last_year

        last_id: int | None = kwargs.get("last_id")

        paths = await self.fetch_paths_async(
            url,
            batch_size=batch_size,
            rows=rows,
            filter=filter,
            session=session,
        )

        return [f"{_url.scheme}://{_url.netloc}{path}" for path in paths]

    def _parse_detail(self, soup):

        info, img_urls = {}, []
        for key, selector in SELECTORs["detail"]["info"].items():
            match (key, soup.select(selector)):
                case (_, []):
                    return ParseHTMLException("공지사항 상세 정보 파싱에 실패했습니다.")

                case ("title", [element, *_]):
                    inner_text = element.get_text(separator=" ", strip=True)
                    inner_text = preprocess.preprocess_text(inner_text)
                    info["title"] = inner_text

                case ("content", [element, *_]):
                    for img in element.select("img"):
                        src = img.get("src")
                        if src:
                            img_urls.append(str(src))
                        img.extract()

                    info["content"] = str(preprocess.clean_html(element).prettify())

                case (_, dls):
                    for dl in dls:
                        dt = dl.select_one("dt:first-child")
                        dd = dl.select_one("dd:nth-child(2)")

                        if not dt or not dd:
                            continue

                        category = dt.get_text(separator=" ", strip=True)
                        content = dd.get_text(separator=" ", strip=True)

                        if category in ["작성일", "date"]:
                            info["date"] = content

                        if category in ["작성자", "name"]:
                            info["author"] = content

        atts = []

        atts += [{"name": info["title"], "url": url} for url in img_urls]

        for e in soup.select(SELECTORs["detail"]["attachments"]):
            anchor = e.select_one("a")
            if not anchor or not anchor.has_attr("href"):
                continue

            name = anchor.get_text(strip=True)
            url = str(anchor["href"])
            atts.append({"name": name, "url": url})

        return NoticeDTO(**{"info": info, "attachments": atts})


class DepartmentNoticeCrawlerService(
    BaseNoticeCrawlerService[NoticeModel],
    BaseDepartmentNoticeService,
):

    def __init__(
        self,
        notice_crawler: NoticeCrawler,
        notice_embedder: NoticeEmbedder,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.notice_crawler = notice_crawler
        self.notice_embedder = notice_embedder

    async def run_crawling_batch(
        self,
        urls: List[str],
        department: str,
        base_url: str,
        category: str,
        is_important: bool = False,
        parse_attachment: bool = False,
    ):
        if type(self.notice_repo) is not NoticeRepository:
            raise ValueError

        logger("Scrape notices...")
        notices = await self.notice_crawler.scrape_detail_async(urls)
        logger("Done.")

        def add_info(notice: NoticeDTO) -> NoticeDTO:
            notice["info"]["department"] = department
            notice["info"]["category"] = category

            notice["attachments"] = [{
                "name": att["name"],
                "url": base_url + att["url"] if att["url"].startswith("/") else att["url"]
            } for att in notice["attachments"]]

            return notice

        notices = list(map(add_info, notices))

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

        notice_models = [self.dto2orm(n, is_important=is_important) for n in notices]
        notice_models = [n for n in notice_models if n is not None]

        with transaction():
            logger("Create notices...")
            notice_models = self.notice_repo.create_all(notice_models)
            dtos = list(map(self.orm2dto, notice_models))
            logger("Done.")

        with transaction():
            logger("Update semester indexes...")
            urls = [dto["url"] for dto in dtos]
            self.add_semester_info(urls=urls)
            logger("Done.")

        return dtos, curr_pages

    async def run_crawling_pipeline(self, **kwargs):

        if type(self.notice_repo) is not NoticeRepository:
            raise ValueError

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
        st_date = datetime.strptime(kwargs.get("st_date", "2000-01-01"), "%Y-%m-%d").date()
        ed_date = datetime.strptime(kwargs.get("ed_date", "2100-12-31"), "%Y-%m-%d").date()

        parse_attachment = kwargs.get("parse_attachment", False)

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
                last_year=st_date,
            )

            with tqdm(total=len(urls), desc=f"[{department}-{category}]") as pbar:
                for st in range(0, len(urls), interval):
                    ed = min(st + interval, len(urls))
                    pbar.set_postfix({'range': f"{st + 1}-{ed}"})

                    _dtos, _ = await self.run_crawling_batch(
                        urls=urls[st:ed],
                        department=department,
                        category=category,
                        base_url=base_url,
                        parse_attachment=parse_attachment,
                    )
                    dtos += _dtos

                    await asyncio.sleep(kwargs.get('delay', 0))

                    pbar.update(len(_dtos))

            logger(f"[{department}-{category}] 주요 공지사항 수집중...")
            important_urls = await self.notice_crawler.scrape_important_urls_async(url=url)
            affected = self.notice_repo.delete_all(urls=important_urls)
            logger(f"[{department}-{category}] {affected} rows deleted (important notice)")

            important_dtos, _ = await self.run_crawling_batch(
                urls=important_urls,
                department=department,
                category=category,
                base_url=base_url,
                is_important=True,
                parse_attachment=parse_attachment,
            )

            common_urls = await self.notice_crawler.scrape_important_urls_async(url=url)
            affected = self.notice_repo.delete_all(urls=common_urls)

            logger(f"[{department}] {affected} rows deleted (important notice)")

            common_dtos, _ = await self.run_crawling_batch(
                urls=common_urls,
                department=department,
                category=category,
                base_url=base_url,
                is_important=True,
                parse_attachment=parse_attachment,
            )

            logger("Done.")

            dtos += important_dtos
            dtos += common_dtos

        return dtos

    def add_semester_info(
        self,
        semesters: List[SemesterType] = [],
        batch_size: int = 500,
        urls: List[str] = [],
    ):
        if type(self.notice_repo) is not NoticeRepository:
            raise ValueError

        if not semesters:
            years = [2023, 2024, 2025]
            types: List[SemesterTypeEnum] = [
                SemesterTypeEnum.spring_semester,
                SemesterTypeEnum.summer_vacation,
                SemesterTypeEnum.fall_semester,
                SemesterTypeEnum.winter_vacation,
            ]
            semesters = [SemesterType(year=year, type_=type_) for year in years for type_ in types]

        if not self.semester_repo:
            raise ValueError("'semester_repo' not provided")

        with transaction():
            semester_models = self.semester_repo.search_semester_by_dtos(semesters)

        affected = 0
        for semester_model in semester_models:

            st, ed = semester_model.st_date, semester_model.ed_date
            date_range = DateRangeType(st_date=st, ed_date=ed)
            total_records = self.notice_repo.search_total_records(date_ranges=[date_range], urls=urls)

            from tqdm import tqdm
            pbar = tqdm(
                range(0, total_records, batch_size),
                desc=f"학기 정보 추가({semester_model.year}-{semester_model.type_})",
            )
            for offset in pbar:
                notices = self.notice_repo.update_semester(semester_model, batch_size, offset, urls=urls)
                affected += len(notices)

        return affected
