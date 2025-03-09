"""학지시 크롤링 스크립트

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

from dependency_injector.wiring import Provide, inject

from containers.crawler.support import SupportCrawlerContainer
import logging

import logging

import warnings

from services.support.service.crawler import SupportCrawlerService

warnings.filterwarnings("ignore")


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
async def main(service: SupportCrawlerService = Provide[SupportCrawlerContainer.support_service]):

    kwargs = init_args()

    try:
        reset = kwargs.get("reset", False)

        await service.run_crawling_pipeline(
            interval=kwargs.get('interval'), delay=kwargs.get('delay'), with_embeddings=True, reset=reset
        )

    except Exception as e:
        logging.exception(f"Error while scraping({e})")


if __name__ == "__main__":
    container = SupportCrawlerContainer()
    container.init_resources()
    container.wire(modules=[__name__])

    asyncio.run(main())
