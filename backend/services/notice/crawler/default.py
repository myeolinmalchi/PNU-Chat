from typing import Callable, List, Tuple
from aiohttp import ClientSession

from bs4 import BeautifulSoup
from services.base.crawler.crawler import ParseHTMLException
from urllib3.util import parse_url

from services.base.crawler import scrape, preprocess
from services.notice import NoticeDTO
from config.logger import _logger
from services.notice.crawler.base import BaseNoticeCrawler

SELECTORs = {
    "list": "div._articleTable > form:nth-child(2) table > tbody > tr:not(.headline)",
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


def _compare_path(path: str, last_id: int | None):
    if not last_id:
        return True

    ss = path.split('/')[4]
    return int(ss) > int(last_id)


from datetime import datetime, date


def _parse_list_table(soup: BeautifulSoup) -> ParseHTMLException | List[Tuple[str, date]]:
    """공지 리스트에서 각 게시글 경로 추출"""

    table = soup.select_one("table")
    if not table:
        return ParseHTMLException("테이블이 존재하지 않습니다.")

    table_rows = soup.select(SELECTORs['list'])

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


async def _fetch_total_pages(
    index_url: str,
    batch_size: int,
    rows: int,
    filter: Callable[[str, date], bool],
    session: ClientSession,
):
    """전체 게시글 경로 추출"""

    total_paths: List[str] = []
    st, ed = 0, batch_size

    while True:
        urls = [f"{index_url}?row={rows}&page={page + 1}" for page in range(st, ed)]

        results_with_error = await scrape.scrape_async(
            url=urls,
            session=session,
            post_process=_parse_list_table,
            delay_range=(1, 2),
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


class NoticeCrawler(BaseNoticeCrawler):

    async def scrape_urls_async(self, **kwargs) -> List[str]:

        url = kwargs.get("url")
        rows = kwargs.get("rows", 500)
        batch_size = kwargs.get("batch_size", 5)
        last_year = kwargs.get("last_year")

        if not url:
            raise ValueError("'url' must be provided")
        session = kwargs.get("session")
        if not session:
            raise ValueError("'session' must be provided")

        _url = parse_url(url)

        last_year = date(kwargs.get("last_year", 2000), 1, 1)

        def filter(path: str, _date: date):
            return _compare_path(path, last_id) and _date > last_year

        last_id: int | None = kwargs.get("last_id")
        paths = await _fetch_total_pages(url, batch_size, rows, filter=filter, session=session)

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
