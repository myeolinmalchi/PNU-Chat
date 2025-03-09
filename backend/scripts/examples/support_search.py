"""학지시 검색 스크립트

Usage:
    $ poetry run python3 scripts/examples/notice_me_search.py --lexical-ratio <lexical-ratio> --query <query> 
        -l, --lexical-ratio: 검색시 lexical socre의 가중치 (0과 1 사이의 실수, default: 0.5)
        -q, --query: 검색 쿼리 (default: None)
"""

import asyncio
import argparse
import logging

from services.support import create_support_service

logger = logging.getLogger(__name__)


async def run(lexical_ratio: float, query: str):
    support_service = create_support_service()

    try:

        search_results = support_service.search_supports_with_filter(query, lexical_ratio=lexical_ratio, count=10)

        for idx, (support, score) in enumerate(search_results):
            print(f"{idx + 1}. {support.title} ({support.category}) (score: {score:.4f})")

    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lexical-ratio", dest="lexical_ratio", default=0.5)
    parser.add_argument("-q", "--query", dest="query", required=True)
    args = parser.parse_args()

    lexical_ratio = float(args.lexical_ratio)
    query = str(args.query)

    asyncio.run(run(lexical_ratio, query))
