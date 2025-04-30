"""학생지원시스템 평가 데이터셋 증강"""

import asyncio
from typing import List
from dependency_injector.wiring import Provide, inject
from openai import AsyncOpenAI
from tqdm import tqdm
from containers.support import SupportContainer
from db.repositories.base import transaction
from evaluation.retrieval.common import Augmentor, Validator
from services.support.service.base import BaseSupportSearchService

from dotenv import load_dotenv

import json

import os

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "datasets", "augmented_queries_v2.jsonl")


@transaction()
@inject
async def run(support_service: BaseSupportSearchService = Provide[SupportContainer.support_service]):

    llm_client = AsyncOpenAI(
        api_key=UPSTAGE_API_KEY,
        base_url="https://api.upstage.ai/v1",
    )

    augmentor = Augmentor(llm_client, "부산대학교 학생지원시스템")
    validator = Validator(llm_client, "부산대학교 학생지원시스템")

    supports = support_service.list_all_supports()

    print("\n==== 학생지원시스템 평가 데이터셋 증강 ====")
    print(f"[Support Service]: {support_service.__class__.__name__}")
    print(f"파일 저장 경로: {FILE_PATH}\n")

    print("file path: " + FILE_PATH)
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for support in tqdm(supports, desc="학생지원시스템"):

            good_examples: List[str] = []
            bad_examples: List[str] = []

            while True:
                title = support["info"]["title"]
                content = str(support["info"]["content"])

                queries = await augmentor.generate(
                    document_title=title,
                    document_content=content,
                    good_example="\n".join(good_examples),
                    bad_example="\n".join(bad_examples),
                )

                results = await validator.validate(title, content, queries)

                if all(result.valid for result in results):
                    data = {"url": support["url"], "queries": queries}
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    break

                bad_examples = []
                good_examples = []

                print("rejected queries:")
                for idx, (query, result) in enumerate(zip(queries, results)):
                    if result.valid or not result.reasons:
                        good_example = f"{idx + 1}. Query: {query}"
                        good_examples.append(good_example)

                        continue

                    reasons = ", ".join(result.reasons)
                    bad_example = (f"{idx + 1}. Query: {query}, "
                                   f"Reason: {reasons}")

                    print(bad_example)
                    bad_examples.append(bad_example)


if __name__ == "__main__":
    support_container = SupportContainer()
    support_container.init_resources()
    support_container.wire(modules=[__name__])

    asyncio.run(run())
