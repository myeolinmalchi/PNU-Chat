from typing import NotRequired, TypedDict, Unpack
from pgvector.sqlalchemy import SparseVector
from config.config import get_professor_urls
from db.common import V_DIM
from db.models import ProfessorModel
from db.models.professor import ProfessorDetailChunkModel
from db.repositories import transaction, ProfessorRepository, UniversityRepository

from services.base import BaseService
from services.base.service import BaseDomainService
from services.professor.embedder import ProfessorEmbedder
from services.professor.crawler import ProfessorCrawlerBase
from services.professor.dto import ProfessorDTO

import asyncio
import logging

logger = logging.getLogger(__name__)


class ProfessorService(BaseDomainService[ProfessorDTO, ProfessorModel]):

    def __init__(
        self, professor_repo: ProfessorRepository, professor_embedder: ProfessorEmbedder,
        professor_crawler: ProfessorCrawlerBase, univ_repo: UniversityRepository
    ):
        self.professor_repo = professor_repo
        self.professor_crawler = professor_crawler
        self.professor_embedder = professor_embedder
        self.univ_repo = univ_repo

    def parse_embeddings(self, dto):
        embeddings = dto.get("embeddings")
        return {
            "detail_chunks": [
                ProfessorDetailChunkModel(
                    detail=e["chunk"], dense_vector=e["dense"], sparse_vector=SparseVector(e["sparse"], V_DIM)
                ) for e in embeddings
            ]
        } if embeddings else {}

    @transaction()
    def dto2orm(self, dto: ProfessorDTO):
        info = dto["info"]
        _professor = {**info}

        department = info["department"]
        department_model = self.univ_repo.find_department_by_name(department)

        if "major" in info:
            major_model = self.univ_repo.find_major(department=department, name=info["major"])
            _professor["major_id"] = major_model.id
            del _professor["major"]

        del _professor["department"]
        _professor["department_id"] = department_model.id
        _professor["url"] = dto["url"]

        _embeddings = self.parse_embeddings(dto)

        return ProfessorModel(**_professor, **_embeddings)

    def orm2dto(self, orm) -> ProfessorDTO:
        ...

    @transaction()
    async def run_full_crawling_pipeline_async(self, **kwargs):
        interval = kwargs.get("interval", 30)
        delay = kwargs.get("delay", 0)
        department = kwargs.get("department")

        if not department:
            raise ValueError("'department' must be contained")

        from tqdm import tqdm

        models = []

        urls = get_professor_urls(department)

        try:

            _urls = []
            for url in urls:
                _urls += self.professor_crawler.scrape_urls(url=url)

            _urls = list(set(_urls))

            pbar = tqdm(range(0, len(_urls), interval), total=len(_urls), desc=f"[{department}]")

            for st in pbar:
                ed = min(st + interval, len(_urls))
                pbar.set_postfix({'range': f"{st + 1} ~ {ed}"})

                __urls = _urls[st:ed]
                dtos = [ProfessorDTO(url=url, info={"department": department}) for url in __urls]
                professors = await self.professor_crawler.scrape_detail_async(dtos)
                professors = await self.professor_embedder.embed_all_async(items=professors, interval=interval)

                professor_models = [self.dto2orm(n) for n in professors]
                professor_models = [n for n in professor_models if n]
                professor_models = self.professor_repo.create_all(professor_models)
                models += professor_models

                pbar.update(interval)

                await asyncio.sleep(delay)
        except TimeoutError as e:
            affected = self.professor_repo.delete_by_department(department)
            logger.exception(f"[{department}] 크롤링에 실패하여 이전 데이터를 초기화 했습니다. ({affected} row deleted)")
            raise e

        return models

    class SearchOptions(TypedDict):
        count: NotRequired[int]
        lexical_ratio: NotRequired[float]

    def search_professors(self, query: str, **opts: Unpack[SearchOptions]):
        from time import time
        st = time()
        embed_result = self.professor_embedder._embed_query(query, chunking=False)
        logger.info(f"embed query: {time() - st:.4f}")

        st = time()
        search_results = self.professor_repo.search_professors_hybrid(
            dense_vector=embed_result["dense"],
            sparse_vector=embed_result["sparse"],
            lexical_ratio=opts.get("lexical_ratio", 0.5),
            k=opts.get("count", 10),
        )
        logger.info(f"hybrid search: {time() - st:.4f}")

        return search_results
