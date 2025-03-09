"""공지사항 게시글 크롤링 스크립트

Usage:
    poetry run python3 scripts/crawler/notice.py
        -i, --interval: 한 번에 스크랩 할 게시글 수 (default: 10)
        -d, --delay: Interval간의 딜레이 (초 단위, default: 0)
        -dp, --department: 학과 (default: ALL)
        -r, --reset: 테이블 초기화 여부 (default: false)
        -rw, --rows: 목록 페이지에서 한 번에 불러올 게시글 수 (기계공학부 제외, default: 500)
"""

import argparse
import asyncio
from typing import Dict

from config.config import get_universities
from containers.crawler.notice import NoticeCrawlerContainer
from db.repositories import transaction
import logging
import time

from services.notice.crawler.me import URLs as ME_URLs

import logging

import warnings

from services.notice import NoticeCrawlerService

warnings.filterwarnings("ignore")

from dependency_injector.wiring import Provide, inject


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval", dest="interval", action="store", default="10")
    parser.add_argument("-d", "--delay", dest="delay", action="store", default="0")
    parser.add_argument("-dp", "--department", dest="department", action="store", default="ALL")
    parser.add_argument("-r", '--reset', dest="reset", action=argparse.BooleanOptionalAction)
    parser.add_argument("-rw", '--rows', dest="rows", action="store", default="500")
    parser.add_argument("-y", '--last-year', dest="last_year", action="store", default="2000")

    args = parser.parse_args()

    kwargs = {
        "interval": int(args.interval),
        "delay": float(args.delay),
        "reset": bool(args.reset),
        "department": str(args.department),
        "rows": int(args.rows),
        "last_year": int(args.last_year),
    }

    return kwargs


@inject
@transaction()
async def main(notice_service: NoticeCrawlerService = Provide[NoticeCrawlerContainer.notice_service]):

    kwargs = init_args()

    try:
        from itertools import chain

        univs = get_universities()
        department = kwargs.get("department")
        departments = [[dep for dep in deps] for deps in univs.values()]
        departments = list(chain(*departments)) if department == "ALL" else [department]

        _type = "me" if department == "기계공학부" else "default"

        reset = kwargs.get("reset", False)
        rows = kwargs.get("rows", 500)
        last_year = kwargs.get("last_year")

        if _type == "default":
            failed_departments: Dict = {}
            for deps in departments:
                try:
                    st = time.time()
                    await notice_service.run_crawling_pipeline(
                        interval=kwargs.get('interval'),
                        delay=kwargs.get('delay'),
                        with_embeddings=True,
                        department=deps,
                        reset=reset,
                        rows=rows,
                        last_year=last_year,
                    )
                    ed = time.time()
                    print(f"[{deps}] total: {ed - st:.0f} sec")
                except Exception as e:
                    failed_departments[department] = e
                    logging.exception(f"[{deps}] 일시적인 오류가 발생했습니다.")
                    continue

            logging.info(f"{len(failed_departments)}개의 학과 크롤링에 실패했습니다.")
            logging.info(f"실패 학과: {failed_departments.keys()}")

        elif _type == "me":
            pass
            """
            for url_key in ME_URLs:
                try:
                    await notice_me_service.run_crawling_pipeline(
                        interval=kwargs.get('interval'),
                        delay=kwargs.get('delay'),
                        url_key=url_key,
                        with_embeddings=True,
                        reset=reset
                    )
                except Exception as e:
                    logging.exception(f"[{url_key}] 일시적인 오류가 발생했습니다. ({e})")
                    continue
            """

    except Exception as e:
        logging.exception(f"Error while scraping({e})")


if __name__ == "__main__":
    notice_container = NoticeCrawlerContainer()
    notice_container.init_resources()
    notice_container.wire(modules=[__name__])

    asyncio.run(main())
