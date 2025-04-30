import asyncio
from typing import List
from aiohttp import ClientSession
from dependency_injector.wiring import Provide, inject
from tqdm import tqdm
from containers.support import SupportContainer
from db.repositories.base import transaction
from evaluation.retrieval.common.schemas import EvalQueryItem
from services.base.embedder import embed_async
from services.support.service.base import BaseSupportSearchService

from dotenv import load_dotenv

import json

import os
import time

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "datasets", "augmented_queries.jsonl")

RRF_K = 20
LEXICAL_RATIO = 0.7
TOP_K = 3


@transaction()
@inject
async def run(support_service: BaseSupportSearchService = Provide[SupportContainer.support_service]):

    print("file path: " + FILE_PATH)

    st = time.time()

    eval_dataset: List[EvalQueryItem] = []

    with open(FILE_PATH, "r", encoding="utf-8") as file:
        for line in file:
            data = EvalQueryItem(**json.loads(line.strip()))
            eval_dataset.append(data)

    fail, success = 0, 0

    async with ClientSession() as session:
        for item in tqdm(eval_dataset, desc=f"Recall@{TOP_K} (학생지원시스템)"):
            query_embeddings = await embed_async(
                texts=item.queries,
                session=session,
                chunking=False,
                html=False,
            )

            futures = [
                support_service.search_supports_async(
                    query="",
                    session=session,
                    embeddings=embeddings,
                    lexical_ratio=LEXICAL_RATIO,
                    count=TOP_K,
                    rrf_k=RRF_K,
                ) for embeddings in query_embeddings
            ]

            retrievaled = await asyncio.gather(*futures)

            for _supports in retrievaled:
                _urls = [sup["url"] for sup in _supports]
                if item.url in _urls:
                    success += 1
                else:
                    fail += 1

    print("\n===== Evaluation Completed ======")
    print(f"Repository: {support_service.support_repo.__class__.__name__}")
    print(f"Service: {support_service.__class__.__name__}")
    print(f"Lexical Ratio: {LEXICAL_RATIO}")
    print(f"RRF K: {RRF_K}")
    print(f"Total Queries: {success + fail}")
    print(f"Recall@{TOP_K}: {success / (success + fail) * 100:.2f}")
    print(f"Total Time: {time.time() - st:.2f} sec")


if __name__ == "__main__":
    support_container = SupportContainer()
    support_container.init_resources()
    support_container.wire(modules=[__name__])

    asyncio.run(run())
