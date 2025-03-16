from abc import abstractmethod
from itertools import chain
from aiohttp import ClientSession
from pgvector.sqlalchemy import SparseVector
from db.common import V_DIM
from db.models.support import SupportAttachmentModel, SupportChunkModel, SupportModel
from db.repositories.base import transaction
from db.repositories.support import SupportRepository
from services.base.embedder import embed_async, rerank_async
from services.base.service import BaseDomainService
from typing import Dict, List, Optional, TypedDict, NotRequired, Unpack

from services.support.crawler import SupportCrawler
from services.support.dto import SupportAttachmentDTO, SupportDTO
import logging

import textwrap

from services.support.embedder import SupportEmbedder

logger = logging.getLogger(__name__)


class BaseSupportService(BaseDomainService[SupportDTO, SupportModel]):

    def __init__(
        self,
        support_repo: SupportRepository,
        support_crawler: SupportCrawler,
        support_embedder: SupportEmbedder,
    ):
        self.support_repo = support_repo
        self.support_crawler = support_crawler
        self.support_embedder = support_embedder

    def dto2orm(self, dto, **_) -> Optional[SupportModel]:

        def parse_info(dto: SupportDTO):
            info = dto.get("info")
            return info if info else {}

        def parse_attachments(dto: SupportDTO):
            attachments = dto.get("attachments")
            embeddings = dto.get("embeddings")
            if not embeddings or not attachments:
                return {"attachments": [], "content_chunks": []}

            att_embeddings = [{
                "chunk_vector": embedding["dense"],
                "chunk_sparse_vector": SparseVector(embedding["sparse"], V_DIM),
            } for embedding in embeddings["attachment_embeddings"]]

            content_chunks = [[SupportChunkModel(
                **_embeddings,
                chunk_content=content,
            ) for content in att["content"]] for _embeddings, att in zip(att_embeddings, attachments)
                              if "content" in att]

            attachment_models = [
                SupportAttachmentModel(name=att["name"], url=att["url"], content_chunks=chunks)
                for att, chunks in zip(attachments, content_chunks)
            ]

            return {"attachments": attachment_models, "content_chunks": list(chain(*content_chunks))}

        def parse_embeddings(dto: SupportDTO):
            embeddings = dto.get("embeddings")
            return {
                "title_vector": embeddings["title_embeddings"]["dense"],
                "title_sparse_vector": SparseVector(embeddings["title_embeddings"]["sparse"], V_DIM),
                "content_chunks": [
                    SupportChunkModel(
                        chunk_content=content_vector["chunk"],
                        chunk_vector=content_vector["dense"],
                        chunk_sparse_vector=SparseVector(content_vector["sparse"], V_DIM),
                    ) for content_vector in embeddings["content_embeddings"]
                    if "chunk" in content_vector and content_vector["chunk"] is not None
                ]
            } if embeddings else {}

        info = parse_info(dto)
        attachments = parse_attachments(dto)
        embeddings = parse_embeddings(dto)

        if not info:
            return None

        support_dict = {
            **info, "attachments": attachments["attachments"],
            "title_vector": embeddings["title_vector"],
            "title_sparse_vector": embeddings["title_sparse_vector"],
            "content_chunks": [*embeddings["content_chunks"], *attachments["content_chunks"]],
            "url": dto["url"]
        }

        return SupportModel(**support_dict)

    def orm2dto(self, orm, **_):
        #attachments = [{"name": att.name, "url": att.url} for att in orm.attachments]
        info = {
            "title": orm.title,
            "sub_category": orm.sub_category,
            "category": orm.category,
            "content": [],
        }
        return SupportDTO(**{"info": info, "attachments": [], "url": orm.url})

    def attachment2context(self, dto: SupportAttachmentDTO) -> Optional[str]:
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

    def dto2context(self, dto: SupportDTO) -> str:
        info = dto.get("info")
        att_contexts = [self.attachment2context(att) for att in dto["attachments"]]
        att_contexts = [att for att in att_contexts if att]

        return textwrap.dedent(
            f"""\
            <Support>
                <title>{info["title"]}</title>
                <metadata>
                    <url>{dto["url"]}</url>
                    <category>{info["category"]}</category>
                    <sub_category>{info["sub_category"]}</sub_category>
                    <title>{info["title"]}</title>
                </metadata>
                <attachments>
                    {"\n".join(att_contexts)}
                </attachments>
                <content>
                    {"\n".join(info["content"])}
                </content>
            </Support>"""
        )


class BaseSupportSearchService(BaseSupportService):

    class SearchOptions(TypedDict):
        count: NotRequired[int]
        lexical_ratio: NotRequired[float]

    @abstractmethod
    async def search_supports_async(
        self,
        query: str,
        session: Optional[ClientSession] = None,
        **opts: Unpack[SearchOptions],
    ) -> List[SupportDTO]:
        pass


class SupportServiceV1(BaseSupportSearchService):

    @transaction()
    async def search_supports_async(self, query, session=None, **opts):
        """search without reranker"""

        if not session:
            raise ValueError("'session' must be provided")

        embed_result = await embed_async(
            query,
            session=session,
            chunking=False,
            html=False,
        )

        chunks = self.support_repo.search_supports_hybrid_v2(
            dense_vector=embed_result["dense"],
            sparse_vector=embed_result["sparse"],
            lexical_ratio=opts.get("lexical_ratio", 0.5),
            k=opts.get("count", 5),
        )

        support_dict: Dict[int, SupportDTO] = {}

        for chunk in chunks:
            attachment_model = chunk.attachment
            support_id = chunk.support_id

            if support_id not in support_dict:
                dto = self.orm2dto(chunk.support)
                support_dict[support_id] = dto
            else:
                dto = support_dict[support_id]

            if not attachment_model:
                assert isinstance(dto["info"]["content"], list)
                dto["info"]["content"].append(chunk.chunk_content)

            else:
                dto["attachments"].append(
                    SupportAttachmentDTO(
                        name=attachment_model.name,
                        url=attachment_model.url,
                        content=chunk.chunk_content,
                    )
                )

        return list(support_dict.values())


class SupportServiceV2(BaseSupportSearchService):

    @transaction()
    async def search_supports_async(self, query, session=None, **opts):

        if not session:
            raise ValueError("'session' must be provided")

        embed_result = await embed_async(query, session=session, chunking=False)
        assert not isinstance(embed_result, list)

        pre_ranked = self.support_repo.search_supports_hybrid_v2(
            dense_vector=embed_result["dense"],
            sparse_vector=embed_result["sparse"],
            lexical_ratio=opts.get("lexical_ratio", 0.5),
            k=opts.get("top_k", 20),
        )

        texts = [support.chunk_content for support in pre_ranked]
        ranks = await rerank_async(query, texts, session=session)
        ranks = sorted(ranks, key=lambda res: res["score"], reverse=True)[:opts.get("count", 5)]

        ranked_dict: Dict[int, SupportDTO] = {}

        for rank in ranks:
            chunk = pre_ranked[rank["index"]]
            attachment_model = chunk.attachment
            support_id = chunk.support_id

            if support_id not in ranked_dict:
                dto = self.orm2dto(chunk.support)
                ranked_dict[support_id] = dto
            else:
                dto = ranked_dict[support_id]

            if not attachment_model:
                assert isinstance(dto["info"]["content"], list)
                dto["info"]["content"].append(chunk.chunk_content)

            else:
                dto["attachments"].append(
                    SupportAttachmentDTO(
                        name=attachment_model.name,
                        url=attachment_model.url,
                        content=chunk.chunk_content,
                    )
                )

        return list(ranked_dict.values())
