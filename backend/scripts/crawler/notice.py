"""공지사항 게시글 크롤링 스크립트

Usage:
    poetry run python3 scripts/crawler/notice.py
        -i, --interval: 한 번에 스크랩 할 게시글 수 (default: 10)
        -d, --delay: Interval간의 딜레이 (초 단위, default: 0)
        -dp, --department: 학과 (default: ALL)
        -r, --reset: 테이블 초기화 여부 (default: false)
        -rw, --rows: 목록 페이지에서 한 번에 불러올 게시글 수 (기계공학부 제외, default: 500)
        -y, --last-year: 마지막 년도
        -pa, --parse-attachment: 첨부파일 파싱 여부
"""

import argparse
import asyncio
from typing import Dict

from config.config import get_universities
from containers.crawler.notice import NoticeCrawlerContainer
from db.repositories import transaction
import logging
import time

from services.notice.crawler.default import DepartmentNoticeCrawlerService

import logging

import warnings
from config.logger import _logger
from services.notice.crawler.me import MENoticeCrawlerService

warnings.filterwarnings("ignore")

logger = _logger(__name__)

from dependency_injector.wiring import Provide, inject


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval", dest="interval", action="store", default="10")
    parser.add_argument("-d", "--delay", dest="delay", action="store", default="0")
    parser.add_argument("-dp", "--department", dest="department", action="store", default="ALL")
    parser.add_argument("-r", '--reset', dest="reset", action=argparse.BooleanOptionalAction)
    parser.add_argument("-rw", '--rows', dest="rows", action="store", default="500")
    parser.add_argument("-y", '--last-year', dest="last_year", action="store", default="2000")
    parser.add_argument("-pa", '--parse-attachment', dest="parse_attachment", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    kwargs = {
        "interval": int(args.interval),
        "delay": float(args.delay),
        "reset": bool(args.reset),
        "department": str(args.department),
        "rows": int(args.rows),
        "last_year": int(args.last_year),
        "parse_attachment": bool(args.parse_attachment),
    }

    return kwargs


@inject
@transaction()
async def main(
    notice_service: DepartmentNoticeCrawlerService = Provide[NoticeCrawlerContainer.notice_service],
    me_notice_service: MENoticeCrawlerService = Provide[NoticeCrawlerContainer.me_notice_crawler],
):

    kwargs = init_args()

    try:
        from itertools import chain

        univs = get_universities()
        department_str: str = kwargs.get("department", "ALL")
        departments = [[dep for dep in deps] for deps in univs.values()]
        departments = list(chain(*departments)) if department_str == "ALL" else department_str.split(",")

        reset = kwargs.get("reset", False)
        rows = kwargs.get("rows", 500)
        last_year = kwargs.get("last_year")
        parse_attachment = kwargs.get("parse_attachment")

        failed_departments: Dict = {}
        for _dep in departments:
            try:
                if _dep == "기계공학부":
                    await me_notice_service.run_crawling_pipeline(
                        interval=kwargs.get('interval'),
                        delay=kwargs.get('delay'),
                        reset=reset,
                        rows=rows,
                        last_year=last_year,
                        parse_attachment=parse_attachment
                    )
                else:
                    st = time.time()
                    await notice_service.run_crawling_pipeline(
                        interval=kwargs.get('interval'),
                        delay=kwargs.get('delay'),
                        department=_dep,
                        reset=reset,
                        rows=rows,
                        last_year=last_year,
                        parse_attachment=parse_attachment
                    )
                    ed = time.time()
                    logger(f"[{_dep}] total: {ed - st:.0f} sec")

            except Exception as e:
                failed_departments[_dep] = e
                logger(f"[{_dep}] 일시적인 오류가 발생했습니다.", logging.ERROR)
            continue

    except Exception as e:
        logging.exception(f"Error while scraping({e})")


if __name__ == "__main__":
    notice_container = NoticeCrawlerContainer()
    notice_container.init_resources()
    notice_container.wire(modules=[__name__])

    asyncio.run(main())
