import asyncio
from typing import Callable, List, Optional, Tuple
from urllib.parse import parse_qs

from aiohttp import ClientSession
from tqdm import tqdm

from db.models.calendar import SemesterTypeEnum
from db.models.notice import PNUNoticeModel
from db.repositories.base import transaction
from db.repositories.notice import PNUNoticeRepository
from services.base import ParseHTMLException
from services.base.crawler import preprocess, scrape

from urllib3.util import parse_url

from services.base.types.calendar import DateRangeType, SemesterType
from services.notice import NoticeDTO
from config.logger import _logger
from services.notice.base import BasePNUNoticeService
from services.notice.crawler.base import BaseNoticeCrawler, BaseNoticeCrawlerService
from services.notice.embedder import NoticeEmbedder

SELECTORs = {
    "list": "tr:not(.isnotice)",
    "list_important": "tr.isnotice",
    "detail": {
        "info": {
            "title": "#board-wrap > div.board-view-head > div.board-view-title > h4",
            "content": "#boardContents",
            "autor": "#board-wrap > div.board-view-head > div.board-view-title > div > span:nth-child(1)",
            "date": "#board-wrap > div.board-view-head > div.board-view-title > div > span:nth-child(2)"
        },
        "attachments": "#board-wrap > div:nth-child(3) > div > div > ul > li"
    }
}

logger = _logger(__name__)

from datetime import datetime, date

BASE_URL = "https://www.pusan.ac.kr"
NOTICE_INDEX_URL = f"{BASE_URL}/kor/CMS/Board/Board.do"
M_CODE = "MN095"


class PNUNoticeCrawler(BaseNoticeCrawler):

    def _parse_paths_from_table_element(self, table_element, **kwargs):

        table = table_element.select_one("table.board-list-table")

        if not table:
            return ParseHTMLException("<table>이 존재하지 않습니다.")

        is_important = kwargs.get("is_important", False)
        table_rows = table_element.select(SELECTORs['list_important' if is_important else 'list'])

        results = []

        for row in table_rows:
            anchor = row.select_one("td.subject > p.stitle > a")

            if anchor is None or not anchor.has_attr("href"):
                continue

            date = row.select_one("td.date")

            if not date:
                continue

            date_str = date.get_text(strip=True)
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            href = str(anchor["href"])
            results.append((href, date))

        return results

    def _validate_detail_path(self, path, **kwargs) -> bool:

        last_id: int | None = kwargs.get("last_id")

        if last_id is None:
            return True

        parsed = parse_url(path)
        queries = parse_qs(parsed.query)
        board_seq = queries.get("board_seq")

        if board_seq is None or len(board_seq) != 1:
            return False

        return int(board_seq[0]) > int(last_id)

    async def fetch_paths_async(
        self,
        index_url: str,
        batch_size: int,
        filter: Callable[[str, date], bool],
        delay_range: Tuple[float, float] = (1, 2),
        session: Optional[ClientSession] = None,
        **_,
    ) -> List[str]:
        """전체 게시글 경로 추출"""

        if not session:
            raise ValueError("'session' must be provided")

        total_paths: List[str] = []
        st, ed = 0, batch_size

        while True:
            urls = [f"{index_url}&page={page + 1}" for page in range(st, ed)]

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

    async def scrape_important_urls_async(self, **kwargs) -> List[str]:
        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        parse_paths = lambda soup: self._parse_paths_from_table_element(soup, is_important=True)

        results_with_error = await scrape.scrape_async(
            url=[NOTICE_INDEX_URL + f"?mCode={M_CODE}"],
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

        return [f"{NOTICE_INDEX_URL}{path}" for path in paths]

    async def scrape_urls_async(self, **kwargs) -> List[str]:

        batch_size = kwargs.get("batch_size", 10)
        session = kwargs.get("session")

        if not session:
            raise ValueError("'session' must be provided")

        def filter(path: str, _):
            return self._validate_detail_path(path, last_id=last_id)

        last_id: int | None = kwargs.get("last_id")
        paths = await self.fetch_paths_async(
            NOTICE_INDEX_URL + f"?mCode={M_CODE}",
            batch_size=batch_size,
            filter=filter,
            session=session,
        )

        return [f"{NOTICE_INDEX_URL}{path}" for path in paths]

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

                case ("author", [element, *_]):
                    inner_text = element.get_text(separator=" ", strip=True)
                    inner_text = inner_text.replace("작성자 ", "")
                    inner_text = preprocess.preprocess_text(inner_text)
                    info["author"] = inner_text

                case ("date", [element, *_]):
                    inner_text = element.get_text(separator=" ", strip=True)
                    inner_text = inner_text.replace("작성일자 ", "")
                    date = datetime.strptime(inner_text, "%Y-%m-%d").date()
                    info["date"] = date

        atts = []

        atts += [{"name": info["title"], "url": url} for url in img_urls]

        for e in soup.select(SELECTORs["detail"]["attachments"]):
            anchor = e.select_one("a")
            if not anchor or not anchor.has_attr("href"):
                continue

            txt = list(anchor.children)[-1]
            name = txt.get_text(strip=True)
            url = str(anchor["href"])
            atts.append({"name": name, "url": url})

        return NoticeDTO(**{"info": info, "attachments": atts})


class PNUNoticeCrawlerSerivce(
    BaseNoticeCrawlerService[PNUNoticeModel],
    BasePNUNoticeService,
):

    def __init__(
        self,
        notice_crawler: PNUNoticeCrawler,
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
        is_important: bool = False,
        parse_attachment: bool = True,
    ) -> Tuple[List[NoticeDTO], int]:

        if type(self.notice_repo) is not PNUNoticeRepository:
            raise ValueError

        logger("Scrape notices...")
        notices = await self.notice_crawler.scrape_detail_async(urls)
        logger("Done.")

        def add_info(notice: NoticeDTO, **kwargs) -> NoticeDTO:
            for key, value in kwargs.items():
                notice["info"][key] = value

            notice["attachments"] = [{
                "name": att["name"],
                "url": BASE_URL + att["url"] if att["url"].startswith("/") else att["url"]
            } for att in notice["attachments"]]

            return notice

        notices = list(map(lambda notice: add_info(notice=notice), notices))

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
        notice_models = [n for n in notice_models if n]

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

        last_id = None

        if kwargs.get("reset", False):
            affected = self.notice_repo.delete_all()
            logger(f"{affected} rows deleted.")

        else:
            last_notice = self.notice_repo.find_last_notice()
            if last_notice:
                last_path = parse_url(last_notice.url).path
                if not last_path:
                    raise ValueError(f"잘못된 url입니다: {last_notice.url}")
                last_id = int(last_path.split("=")[5])

        interval = kwargs.get('interval', 30)

        urls = await self.notice_crawler.scrape_urls_async(last_id=last_id)

        dtos: List[NoticeDTO] = []

        with tqdm(total=len(urls)) as pbar:
            for st in range(0, len(urls), interval):
                ed = min(st + interval, len(urls))
                pbar.set_postfix({'range': f"{st + 1}-{ed}"})

                _dtos, _ = await self.run_crawling_batch(urls=urls[st:ed], parse_attachment=True)
                dtos += _dtos

                await asyncio.sleep(kwargs.get('delay', 0))

                pbar.update(len(_dtos))

        logger(f"주요 공지사항 수집중...")
        important_urls = await self.notice_crawler.scrape_important_urls_async()
        affected = self.notice_repo.delete_all(urls=important_urls)
        logger(f"{affected} rows deleted (important notice)")

        important_dtos, _ = await self.run_crawling_batch(
            urls=important_urls,
            is_important=True,
            parse_attachment=True,
        )

        logger("Done.")

        dtos += important_dtos

        return dtos

    def add_semester_info(
        self,
        semesters: List[SemesterType] = [],
        batch_size: int = 500,
        urls: List[str] = [],
    ) -> int:
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
