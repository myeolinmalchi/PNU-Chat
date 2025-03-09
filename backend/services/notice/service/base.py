from abc import abstractmethod
import logging
import textwrap
from typing import Dict, List, NotRequired, Optional, Required, TypedDict, Unpack
from aiohttp import ClientSession
from pgvector.sqlalchemy import SparseVector

from db.common import V_DIM
from db.models import AttachmentModel, NoticeChunkModel, NoticeModel
from db.models.university import DepartmentModel

from db.repositories.base import transaction
from db.repositories.calendar import SemesterRepository
from db.repositories.notice import INoticeRepository
from db.repositories.university import UniversityRepository

from services.base.embedder import embed_async, rerank_async
from services.base.service import BaseDomainService
from services.base.types.calendar import SemesterType
from services.notice.dto import AttachmentDTO, NoticeDTO
from services.notice.embedder import NoticeEmbedder

from datetime import datetime

from itertools import chain

from services.university.service.calendar import CalendarService

logger = logging.getLogger(__name__)


class BaseNoticeService(BaseDomainService[NoticeDTO, NoticeModel]):

    def __init__(
        self,
        notice_repo: INoticeRepository,
        notice_embedder: NoticeEmbedder,
        calendar_service: CalendarService,
        university_repo: UniversityRepository,
        semester_repo: Optional[SemesterRepository] = None
    ):
        self.notice_repo = notice_repo
        self.notice_embedder = notice_embedder
        self.calendar_service = calendar_service
        self.university_repo = university_repo
        self.semester_repo = semester_repo

    def _parse_info(self, dto: NoticeDTO):
        info = dto.get("info")
        return info if info else {}

    def _parse_attachments(self, dto: NoticeDTO):

        attachments = dto.get("attachments")
        embeddings = dto.get("embeddings")

        if not embeddings or not attachments:
            return {"attachments": [], "content_chunks": []}

        chunk_models = [[
            NoticeChunkModel(
                chunk_vector=embedding["dense"],
                chunk_sparse_vector=SparseVector(embedding["sparse"], V_DIM),
                chunk_content=content,
            ) for content in att["content"]
        ] for embedding, att in zip(embeddings["attachment_embeddings"], attachments) if "content" in att]

        attachment_models = [
            AttachmentModel(name=att["name"], url=att["url"], content_chunks=chunks)
            for att, chunks in zip(attachments, chunk_models)
        ]

        return {
            "attachments": attachment_models,
            "content_chunks": list(chain(*chunk_models)),
        }

    def _parse_embeddings(self, dto: NoticeDTO):
        embeddings = dto.get("embeddings")
        if not embeddings:
            return {}

        title_embeddings = embeddings["title_embeddings"]
        content_embeddings = embeddings["content_embeddings"]
        content_embeddings = content_embeddings if isinstance(content_embeddings, list) else [content_embeddings]
        chunk_models = [
            NoticeChunkModel(
                chunk_content=content_vector["chunk"],
                chunk_vector=content_vector["dense"],
                chunk_sparse_vector=SparseVector(content_vector["sparse"], V_DIM),
            ) for content_vector in content_embeddings if "chunk" in content_vector
        ]

        return {
            "title_vector": title_embeddings["dense"],
            "title_sparse_vector": SparseVector(title_embeddings["sparse"], V_DIM),
            "content_chunks": chunk_models
        } if embeddings else {}

    def dto2orm(self, dto: NoticeDTO) -> Optional[NoticeModel]:
        info = self._parse_info(dto)
        attachments = self._parse_attachments(dto)
        embeddings = self._parse_embeddings(dto)

        if not info:
            return None

        department_model = self.university_repo.find_department_by_name(info["department"])

        if type(department_model) is not DepartmentModel:
            raise ValueError(f"[]")

        del info["department"] # type: ignore

        notice_dict = {
            **info,
            "attachments": attachments["attachments"],
            "title_vector": embeddings["title_vector"],
            "title_sparse_vector": embeddings["title_sparse_vector"],
            "content_chunks": [*embeddings["content_chunks"], *attachments["content_chunks"]],
            "department_id": department_model.id,
            "url": dto["url"],
        }

        return NoticeModel(**notice_dict)

    def orm2dto(self, orm: NoticeModel) -> NoticeDTO:
        attachments = [{"name": att.name, "url": att.url} for att in orm.attachments]
        info = {
            "title": orm.title,
            "content": orm.content,
            "category": orm.category,
            "department": orm.department.name,
            "date": str(orm.date),
            "author": orm.author
        }
        return NoticeDTO(**{"info": info, "attachments": attachments, "url": orm.url})

    def attachment2context(self, dto: AttachmentDTO) -> Optional[str]:
        return textwrap.dedent(
            f"""\
            <attachment>
                <name>{dto["name"]}</name>
                <url>{dto['url']}</url>
                <content>
                    {dto["content"]}
                </content>
            </attachment>"""
        ) if "content" in dto else None

    def dto2context(self, dto: NoticeDTO) -> str:
        info = dto["info"]
        att_contexts = [self.attachment2context(att) for att in dto["attachments"]]
        att_contexts = [att for att in att_contexts if att]
        att_content = textwrap.dedent(
            f"""
            <attachments>
                {"\n".join(att_contexts)}
            </attachments>"""
        ) if len(att_contexts) > 0 else ""

        return textwrap.dedent(
            f"""\
            <Notice>
                <title>{info["title"]}</title>
                <metadata>
                    <url>{dto["url"]}</url>
                    <date>{info["date"]}</date>
                    <author>{info["author"]}</author>
                    <department>{info["department"]}</department>
                    <category>{info["category"]}</category>
                </metadata>
                {att_content}
                <content>
                    {info["content"]}
                </content>
            </Notice>
            """
        )


class BaseNoticeSearchService(BaseNoticeService):

    class SearchOptions(TypedDict, total=False):
        top_k: NotRequired[int]
        count: NotRequired[int]
        threshold: NotRequired[float]
        lexical_ratio: NotRequired[float]
        semesters: NotRequired[List[SemesterType]]
        departments: Required[List[str]]

    @abstractmethod
    async def search_notices_async(
        self,
        query: str,
        session: Optional[ClientSession] = None,
        **opts: Unpack[SearchOptions],
    ) -> List[NoticeDTO]:
        pass


class NoticeServiceV1(BaseNoticeSearchService):

    async def search_notices_async(self, query, session=None, **opts):
        """search without reranker"""

        if not session:
            raise ValueError("'session' must be provided")

        if not self.semester_repo:
            raise ValueError("'NoticeService.semester_repo' must be provided")

        embed_result = await embed_async(query, session=session, chunking=False)
        assert not isinstance(embed_result, list)

        departments = opts['departments']
        semester_ids = []
        with transaction():
            if "semesters" not in opts:
                now = datetime.now()
                semesters = self.calendar_service.get_semester(now.year, now.month, now.day)
                semester_ids = [s["semester_id"] for s in semesters if "semester_id" in s]

            else:
                semesters = opts["semesters"]
                semester_models = self.semester_repo.search_semester_by_dtos(semesters)
                related_semester_models = [self.calendar_service.get_related_semester(orm) for orm in semester_models]
                related_semester_models = [orm for orm in related_semester_models if orm]
                semester_ids = [s.id for s in [*semester_models, *related_semester_models]]

        with transaction():
            chunks = self.notice_repo.search_chunks_hybrid(
                dense_vector=embed_result["dense"],
                sparse_vector=embed_result["sparse"],
                lexical_ratio=opts.get("lexical_ratio", 0.5),
                semester_ids=semester_ids,
                departments=departments,
                k=opts.get("count", 5),
            )
            notice_dict: Dict[int, NoticeDTO] = {}

            for chunk in chunks:
                attachment_model = chunk.attachment
                notice_id = chunk.notice_id

                if notice_id not in notice_dict:
                    dto = self.orm2dto(chunk.notice)
                    notice_dict[notice_id] = dto
                else:
                    dto = notice_dict[notice_id]

                if not attachment_model:
                    dto["info"]["content"] = chunk.chunk_content

                else:
                    dto["attachments"].append(
                        AttachmentDTO(
                            name=attachment_model.name,
                            url=attachment_model.url,
                            content=chunk.chunk_content,
                        )
                    )

        return list(notice_dict.values())


class NoticeServiceV2(BaseNoticeSearchService):

    async def search_notices_async(self, query, session=None, **opts):

        if not session:
            raise ValueError("'session' must be provided")

        if not self.semester_repo:
            raise ValueError("'NoticeService.semester_repo' must be provided")

        embed_result = await embed_async(query, session=session, chunking=False)
        assert not isinstance(embed_result, list)

        departments = opts['departments']

        semester_ids = []
        with transaction():
            if "semesters" not in opts:
                now = datetime.now()
                semesters = self.calendar_service.get_semester(now.year, now.month, now.day)
                semester_ids = [s["semester_id"] for s in semesters if "semester_id" in s]

            else:
                semesters = opts["semesters"]
                semester_models = self.semester_repo.search_semester_by_dtos(semesters)
                semester_ids = [s.id for s in semester_models]

        with transaction():
            pre_ranked = self.notice_repo.search_chunks_hybrid(
                dense_vector=embed_result["dense"],
                sparse_vector=embed_result["sparse"],
                lexical_ratio=opts.get("lexical_ratio", 0.5),
                semester_ids=semester_ids,
                departments=departments,
                k=opts.get("top_k", 20),
            )

            texts = [notice.chunk_content for notice in pre_ranked]
            ranks = await rerank_async(query, texts, session=session)
            ranks = sorted(ranks, key=lambda res: res["score"], reverse=True)[:opts.get("count", 5)]
            ranks = filter(lambda rank: rank["score"] >= opts.get("threshold", 0.5), ranks)

            ranked_dict: Dict[int, NoticeDTO] = {}

            for rank in ranks:
                chunk = pre_ranked[rank["index"]]
                attachment_model = chunk.attachment
                notice_id = chunk.notice_id

                if notice_id not in ranked_dict:
                    dto = self.orm2dto(chunk.notice)
                    ranked_dict[notice_id] = dto
                else:
                    dto = ranked_dict[notice_id]

                if not attachment_model:
                    #assert isinstance(dto["info"]["content"], list)
                    dto["info"]["content"] = chunk.chunk_content

                else:
                    dto["attachments"].append(
                        AttachmentDTO(
                            name=attachment_model.name,
                            url=attachment_model.url,
                            content=chunk.chunk_content,
                        )
                    )

        return list(ranked_dict.values())
