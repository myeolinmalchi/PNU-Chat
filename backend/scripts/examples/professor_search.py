"""공지사항(기계공학부) 검색 스크립트

Usage:
    $ poetry run python3 scripts/examples/notice_me_search.py --lexical-ratio <lexical-ratio> --query <query> 
        -l, --lexical-ratio: 검색시 lexical socre의 가중치 (0과 1 사이의 실수, default: 0.5)
        -q, --query: 검색 쿼리 (default: None)
"""

import asyncio
import argparse
import logging
from typing import List

from services.professor import create_professor_service

logger = logging.getLogger(__name__)


async def run(lexical_ratio: float, query: str, departments: List[str]):
    professor_service = create_professor_service()

    try:
        search_results = professor_service.search_professors(query, lexical_ratio=lexical_ratio)

        for idx, (professor, score) in enumerate(search_results):
            print(f"[{idx + 1}] {professor.name} (score: {score:.4f})")

    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lexical-ratio", dest="lexical_ratio", default=0.5)
    parser.add_argument("-q", "--query", dest="query", required=True)
    parser.add_argument("-dp", "--departments", dest="departments", action="store", default="ALL")
    args = parser.parse_args()

    lexical_ratio = float(args.lexical_ratio)
    query = str(args.query)
    departments = str(args.departments)
    departments = list(departments.split(','))
    asyncio.run(run(lexical_ratio, query, departments))
