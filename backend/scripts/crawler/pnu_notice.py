"""공지사항 게시글 크롤링 스크립트

Usage:
    poetry run python3 scripts/crawler/notice.py
        -i, --interval: 한 번에 스크랩 할 게시글 수 (default: 10)
        -d, --delay: Interval간의 딜레이 (초 단위, default: 0)
        -r, --reset: 테이블 초기화 여부 (default: false)
"""

import argparse
import asyncio

from containers.crawler.pnu_notice import PNUNoticeCrawlerContainer
from db.repositories import transaction
import logging

from services.notice.crawler.base import BaseNoticeCrawlerService

import logging

import warnings

warnings.filterwarnings("ignore")

from dependency_injector.wiring import Provide, inject


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval", dest="interval", action="store", default="10")
    parser.add_argument("-d", "--delay", dest="delay", action="store", default="0")
    parser.add_argument("-r", '--reset', dest="reset", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    kwargs = {
        "interval": int(args.interval),
        "delay": float(args.delay),
        "reset": bool(args.reset),
    }

    return kwargs


@inject
@transaction()
async def main(notice_service: BaseNoticeCrawlerService = Provide[PNUNoticeCrawlerContainer.notice_service]):

    kwargs = init_args()

    try:
        reset = kwargs.get("reset", False)

        try:
            await notice_service.run_crawling_pipeline(
                interval=kwargs.get('interval'),
                delay=kwargs.get('delay'),
                reset=reset,
            )
        except Exception as e:
            logging.exception(f"일시적인 오류가 발생했습니다.")

    except Exception as e:
        logging.exception(f"Error while scraping({e})")


if __name__ == "__main__":
    notice_container = PNUNoticeCrawlerContainer()

    notice_container.init_resources()
    notice_container.wire(modules=[__name__])

    asyncio.run(main())
