"""기계공학부 공지사항 크롤러"""

import asyncio
from datetime import date, datetime
from typing import List
from urllib.parse import parse_qs

from bs4 import BeautifulSoup
import bs4
from tqdm import tqdm
from urllib3.util import parse_url

from db.models.calendar import SemesterTypeEnum
from db.models.notice import NoticeModel
from db.repositories.base import transaction
from db.repositories.notice import NoticeRepository
from services.base.crawler import preprocess, scrape
from services.base.crawler.crawler import ParseHTMLException
from services.base.types.calendar import DateRangeType, SemesterType
from services.notice import NoticeDTO

import re

from services.notice.base import BaseDepartmentNoticeService
from services.notice.crawler.base import BaseNoticeCrawler, BaseNoticeCrawlerService
from services.notice.embedder import NoticeEmbedder
from config.logger import _logger

logger = _logger(__name__)

URLs = {
    "공지/학부": {
        "path": "/new/sub05/sub01_01.asp",
        "db": "hakbunotice"
    },
    "공지/대학원": {
        "path": "/new/sub05/sub01_02.asp",
        "db": "gradnotice"
    },
    "공지/장학": {
        "path": "/new/sub05/sub01_05.asp",
        "db": "supervision"
    },
    "공지/홍보": {
        "path": "/new/sub05/sub01_03.asp",
        "db": "notice2"
    },
    "학부_소식": {
        "path": "/new/sub05/sub02.asp",
        "db": "hakbunews"
    },
    "언론_속_학부": {
        "path": "/new/sub05/sub03.asp",
        "db": "media"
    },
    "세미나": {
        "path": "/new/sub05/sub04.asp",
        "db": "seminar"
    },
    "취업정보": {
        "path": "/new/sub05/sub05.asp",
        "db": "recruit"
    },
}

SELECTORs = {
    "list": "#contents > div > div > div > div.board-list02 > table > tbody > tr:not(.notice)",
    "list_important": "#contents > div > div > div > div.board-list02 > table > tbody > tr.notice",
    "detail": {
        "info": {
            "title": "#contents > div > div > div.board-view dl:nth-child(1) > dd",
            "date": "#contents > div > div > div.board-view > dl:nth-child(2) > dd",
            "author": "#contents > div > div > div.board-view > dl:nth-child(3) > dd",
            "content": "#contents > div > div > div.board-contents.clear",
        },
        "attachments": "#contents > div > div > div.board-view > dl.half-box01.none > dd",
    },
}

DOMAIN = "https://me.pusan.ac.kr"
DEPARTMENT = "기계공학부"


class MENoticeCrawler(BaseNoticeCrawler):

    async def scrape_important_urls_async(self, **kwargs) -> List[str]:
        """게시글 url 목록 불러오기"""
        url_key = kwargs.get("url_key")

        if not url_key:
            raise ValueError("'url_key' must be contained")

        if url_key not in URLs.keys():
            raise ValueError("존재하지 않는 카테고리입니다.")

        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        url = f"{DOMAIN}{URLs[url_key]['path']}"

        seqs = await scrape.scrape_async(
            url=url,
            session=session,
            post_process=self._parse_important_seqs,
            delay_range=(0, 0),
        )

        path = URLs[url_key]["path"]
        db = URLs[url_key]["db"]

        _urls = [f"{DOMAIN}{path}?db={db}&seq={seq}&page_mode=view" for seq in seqs]

        return _urls

    def _parse_important_seqs(self, soup: BeautifulSoup):
        table_rows = soup.select(SELECTORs["list_important"])

        seqs: List[int] = []
        for row in table_rows:

            anchor = row.select_one("td > a:first-child")
            if anchor is None or not anchor.has_attr("href"):
                continue

            href = str(anchor["href"])
            seq_str = re.search(r"javascript:goDetail\((.*?)\)", href)

            if not seq_str:
                continue

            seq = int(seq_str.group(1))
            seqs.append(seq)

        return seqs

    def _parse_paths_from_table_element(self, table_element, **kwargs):
        table = table_element.select_one("table")

        if not table:
            return ParseHTMLException("<table>이 존재하지 않습니다.")

        is_important = kwargs.get("is_important", False)
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
            results.append((href, date))

        return results

    def _validate_detail_path(self, path, **kwargs) -> bool:
        raise NotImplementedError()

    async def scrape_urls_async(self, **kwargs) -> List[str]:
        """게시글 url 목록 불러오기"""

        url_key = kwargs.get("url_key")
        last_id = kwargs.get("last_id")

        st_date = kwargs.get("st_date")
        ed_date = kwargs.get("ed_date")

        if not url_key:
            raise ValueError("'url_key' must be contained")

        if url_key not in URLs.keys():
            raise ValueError("존재하지 않는 카테고리입니다.")

        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        url = f"{DOMAIN}{URLs[url_key]['path']}"

        # 가장 최신 게시글의 seq
        recent_seq = await scrape.scrape_async(
            url=url,
            session=session,
            post_process=self._parse_last_seq,
        )

        path = URLs[url_key]["path"]
        db = URLs[url_key]["db"]

        last_id = last_id if last_id is not None else 1

        if last_id == recent_seq:
            return []

        url = f"{DOMAIN}{path}?perPage={recent_seq - last_id + 1}"

        _parse_seq_list = lambda soup: self._parse_seq_list(soup, st_date, ed_date)

        seqs = await scrape.scrape_async(url=url, session=session, post_process=_parse_seq_list)

        urls = [f"{DOMAIN}{path}?seq={seq}&db={db}&page_mode=view" for seq in seqs]

        return urls

    def _parse_last_seq(self, soup: BeautifulSoup):
        table_rows = soup.select(SELECTORs["list"])

        for row in table_rows:

            anchor = row.select_one("td > a:first-child")
            if anchor is None or not anchor.has_attr("href"):
                continue

            href = str(anchor["href"])
            seq_str = re.search(r"javascript:goDetail\((.*?)\)", href)

            if seq_str != None:
                seq = int(seq_str.group(1))
                return seq

        raise Exception

    def _parse_seq_list(
        self,
        soup: BeautifulSoup,
        st_date: date | None = None,
        ed_date: date | None = None,
    ) -> List[int]:
        table_rows = soup.select(SELECTORs["list"])

        def tr2seq(table_row: bs4.Tag):
            anchor = table_row.select_one("td > a:first-child")
            if anchor is None or not anchor.has_attr("href"):
                return None

            href = str(anchor["href"])
            seq_str = re.search(r"javascript:goDetail\((.*?)\)", href)

            if seq_str is None:
                return None

            date_element = table_row.select_one("td.date")
            if not date_element:
                return None

            date_str = date_element.get_text(strip=True)

            upload_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if (st_date is not None and upload_date < st_date) or (ed_date is not None and upload_date > ed_date):
                return None

            seq = int(seq_str.group(1))

            return seq

        seq_list = list(map(tr2seq, table_rows))
        seq_list = [seq for seq in seq_list if seq is not None]

        return seq_list

    def _parse_detail(self, soup):

        atts = []
        info, img_urls = {}, []

        content_element = soup.select_one("#contents > div > div div.board-contents.clear")
        if not content_element:
            return ParseHTMLException("공지사항 상세 정보 파싱에 실패했습니다.")

        for img in content_element.select("img"):
            src = img.get("src")
            if src:
                url = str(src).replace("\\", "/").replace("../", "")
                url = url if url.startswith("/") else f"/{url}"
                img_urls.append(f"{DOMAIN}{url}")
            img.extract()

        info["content"] = str(preprocess.clean_html(content_element).prettify())

        for element in soup.select("#contents > div > div > div.board-view dl"):
            dt = element.select_one("dt:first-child")
            dd = element.select_one("dd:nth-child(2)")

            if not dt or not dd:
                continue

            category = dt.get_text(strip=True)

            if category == "제목":
                inner_text = dd.get_text(separator=" ", strip=True)
                inner_text = preprocess.preprocess_text(inner_text)
                info["title"] = inner_text

            elif category == "등록일":
                info["date"] = dd.get_text(separator=" ", strip=True)

            elif category == "작성자":
                info["author"] = dd.get_text(separator=" ", strip=True)

            elif category == "첨부파일":
                for a in dd.select("a"):
                    if not a or not a.has_attr("href"):
                        continue

                    name = a.get_text(strip=True)
                    url = str(a["href"])

                    atts.append({"name": name, "url": url})
        """
        for key, selector in SELECTORs["detail"]["info"].items():
            match (key, soup.select(selector)):
                case (_, []):
                    print(key)
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

                case (_, [element, *_]):
                    info[key] = element.get_text(separator=" ", strip=True)
        """

        atts += [{"name": info["title"], "url": url} for url in img_urls]

        att_element = soup.select_one(SELECTORs["detail"]["attachments"])

        if att_element:
            for a in att_element.select("a"):
                if not a or not a.has_attr("href"):
                    continue

                name = a.get_text(strip=True)
                url = str(a["href"])
                atts.append({"name": name, "url": f"{DOMAIN}{url}"})

        return NoticeDTO(**{"info": info, "attachments": atts})


class MENoticeCrawlerService(
    BaseNoticeCrawlerService[NoticeModel],
    BaseDepartmentNoticeService,
):

    def __init__(
        self,
        notice_crawler: MENoticeCrawler,
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
        category: str,
        is_important: bool = False,
        parse_attachment: bool = False,
    ):
        if type(self.notice_repo) is not NoticeRepository:
            raise ValueError

        if not urls:
            return [], None

        logger("Scrape notices...")
        notices = await self.notice_crawler.scrape_detail_async(urls)
        logger("Done.")

        curr_base_url = "/".join(urls[0].split("/")[:5])

        def add_info(notice: NoticeDTO, **kwargs) -> NoticeDTO:
            for key, value in kwargs.items():
                notice["info"][key] = value

            atts = []

            for att in notice["attachments"]:
                if att["url"].startswith("./"):
                    url = att["url"].replace("./", "/")
                    url = curr_base_url + url
                elif att["url"].startswith("/"):
                    url = DOMAIN + att["url"]
                else:
                    url = att["url"]

                atts.append({"name": att["name"], "url": url})

            notice["attachments"] = atts

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

        reset = kwargs.get("reset", False)
        interval = kwargs.get('interval', 30)
        st_date = datetime.strptime(kwargs.get("st_date", "2000-01-01"), "%Y-%m-%d").date()
        ed_date = datetime.strptime(kwargs.get("ed_date", "2100-12-31"), "%Y-%m-%d").date()

        dtos: List[NoticeDTO] = []

        parse_attachment = kwargs.get("parse_attachment", False)

        for url_key in URLs.keys():

            search_filter = {
                "departments": [DEPARTMENT],
                "categories": [url_key],
            }

            last_id = None
            if reset:
                date_range = DateRangeType(st_date=st_date, ed_date=ed_date)
                affected = self.notice_repo.delete_all(**search_filter, date_ranges=[date_range])
                logger(f"[{DEPARTMENT}-{url_key}] {affected} rows deleted.")

            else:
                last_notice = self.notice_repo.find_last_notice(is_me=True, **search_filter)
                if last_notice:
                    last_id = int(parse_qs(parse_url(last_notice.url).query)["seq"][0])

            urls = await self.notice_crawler.scrape_urls_async(
                url_key=url_key,
                last_id=last_id,
                st_date=st_date,
                ed_date=ed_date,
            )

            with tqdm(total=len(urls), desc=f"[{DEPARTMENT}-{url_key}]") as pbar:
                for st in range(0, len(urls), interval):
                    ed = min(st + interval, len(urls))
                    pbar.set_postfix({'range': f"{st + 1}-{ed}"})

                    _dtos, _ = await self.run_crawling_batch(
                        urls=urls[st:ed],
                        department=DEPARTMENT,
                        category=url_key,
                        parse_attachment=parse_attachment,
                    )
                    dtos += _dtos

                    if len(_dtos) < interval:
                        break

                    await asyncio.sleep(kwargs.get('delay', 0))

                    pbar.update(len(_dtos))

            logger(f"[{DEPARTMENT}-{url_key}] 주요 공지사항 수집중...")
            important_urls = await self.notice_crawler.scrape_important_urls_async(url_key=url_key)
            affected = self.notice_repo.delete_all(urls=important_urls)
            logger(f"[{DEPARTMENT}-{url_key}] {affected} rows deleted (important notice)")

            important_dtos, _ = await self.run_crawling_batch(
                urls=important_urls,
                department=DEPARTMENT,
                category=url_key,
                is_important=True,
            )

            logger("Done.")

            dtos += important_dtos

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
                desc=f"학기 정보 추가({semester_model.year}-{semester_model.type_.value})",
            )
            for offset in pbar:
                notices = self.notice_repo.update_semester(semester_model, batch_size, offset, urls=urls)
                affected += len(notices)

        return affected
