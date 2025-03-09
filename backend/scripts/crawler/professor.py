"""교수님(기계공학부) 크롤링 스크립트

Usage:
    poetry run python3 scripts/crawler/professor.py --category <category> --interval <interval>
        -i, --interval: 한 번에 스크랩 할 게시글 수 (default: 50)
        -c, --category: 공지사항 카테고리 (`services/professor/crawler.py` 참고. default: ALL)
"""

import argparse
import asyncio

from config.config import get_universities
from db.repositories import transaction

import logging

from services.professor import create_professor_service


@transaction()
async def main(**kwargs):
    from itertools import chain

    univs = get_universities()

    department = kwargs.get("department")
    departments = [[dep for dep in deps] for deps in univs.values()]
    departments = list(chain(*departments)
                       ) if department == "ALL" else [department]

    _type = "me" if department == "기계공학부" else "default"

    professor_service = create_professor_service(_type)
    reset = kwargs.get("reset", False)

    for department in departments:
        try:
            await professor_service.run_full_crawling_pipeline_async(
                interval=kwargs.get('interval'),
                delay=kwargs.get('delay'),
                department=department
            )

        except Exception as e:
            logging.exception(f"[{department}] 일시적인 오류가 발생했습니다. ({e})")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--interval", dest="interval", action="store", default="10"
    )
    parser.add_argument(
        "-d", "--delay", dest="delay", action="store", default="0"
    )
    parser.add_argument(
        "-dp", "--department", dest="department", action="store", default="ALL"
    )
    parser.add_argument(
        "-r", '--reset', dest="reset", action=argparse.BooleanOptionalAction
    )

    args = parser.parse_args()

    kwargs = {
        "interval": int(args.interval),
        "delay": float(args.delay),
        "reset": bool(args.reset),
        "department": str(args.department),
    }

    asyncio.run(main(**kwargs))
