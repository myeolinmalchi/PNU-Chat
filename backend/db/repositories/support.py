from typing import Dict, List, Optional
from db.models.support import SupportAttachmentModel, SupportModel, SupportChunkModel
from db.repositories.base import BaseRepository
from pgvector.sqlalchemy import SparseVector
from db.common import V_DIM
from sqlalchemy import func


class SupportRepository(BaseRepository[SupportModel]):

    def delete_all(self):
        affected = self.session.query(SupportModel).delete()
        return affected

    def search_supports_content_hybrid(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[int, float],
        lexical_ratio: float = 0.5,
        k: int = 5,
    ):
        """내용으로 유사도 검색"""
        score_dense = 1 - SupportChunkModel.chunk_vector.max_inner_product(dense_vector)
        score_lexical = -1 * (
            SupportChunkModel.chunk_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )

        score = func.max((score_lexical * lexical_ratio) + score_dense * (1 - lexical_ratio)).label("score")

        query = (
            self.session.query(SupportModel, SupportChunkModel,
                               score).join(SupportModel, SupportModel.id == SupportChunkModel.support_id).group_by(
                                   SupportChunkModel.id
                               ).group_by(SupportModel.id).order_by(score.desc()).limit(k)
        )

        return query.all()

    def search_supports_hybrid_v2(
        self,
        dense_vector: Optional[List[float]] = None,
        sparse_vector: Optional[Dict[int, float]] = None,
        lexical_ratio: float = 0.5,
        rrf_k: int = 120,
        k: int = 5,
    ):
        score_dense_content = 1 - SupportChunkModel.chunk_vector.cosine_distance(dense_vector)
        score_lexical_content = -1 * (
            SupportChunkModel.chunk_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )
        score_content = func.max((score_lexical_content * lexical_ratio) + score_dense_content *
                                 (1 - lexical_ratio)).label("score_content")

        score_dense_title = 1 - SupportModel.title_vector.cosine_distance(dense_vector)
        score_lexical_title = -1 * (
            SupportModel.title_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )
        score_title = ((score_lexical_title * lexical_ratio) + score_dense_title *
                       (1 - lexical_ratio)).label("score_title")

        rank_content = self.session.query(
            SupportChunkModel.id,
            func.row_number().over(order_by=score_content.desc()).label("rank_content"),
        ).group_by(SupportChunkModel.id).join(SupportModel, SupportChunkModel.support_id == SupportModel.id).subquery()

        rank_title = self.session.query(
            SupportChunkModel.id,
            func.row_number().over(order_by=score_title.desc()).label("rank_title"),
        ).join(SupportChunkModel, SupportChunkModel.support_id == SupportModel.id).subquery()

        rrf_score = (1 / (rrf_k + rank_content.c.rank_content) + 1 /
                     (rrf_k + rank_title.c.rank_title)).label("rrf_score")

        query = (
            self.session.query(SupportChunkModel).join(
                rank_content,
                SupportChunkModel.id == rank_content.c.id,
            ).join(
                rank_title,
                SupportChunkModel.id == rank_title.c.id,
            ).order_by(rrf_score.desc()).limit(k)
        )

        return query.all()

    def search_supports_hybrid(
        self,
        dense_vector: Optional[List[float]] = None,
        sparse_vector: Optional[Dict[int, float]] = None,
        lexical_ratio: float = 0.5,
        rrf_k: int = 120,
        k: int = 5,
        **kwargs
    ):

        score_dense_content = 1 - SupportChunkModel.chunk_vector.cosine_distance(dense_vector)
        score_lexical_content = -1 * (
            SupportChunkModel.chunk_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )
        score_content = func.max((score_lexical_content * lexical_ratio) + score_dense_content *
                                 (1 - lexical_ratio)).label("score_content")

        rank_content = (
            self.session.query(
                SupportModel.id,
                func.row_number().over(order_by=score_content.desc()).label("rank_content"),
            ).join(
                SupportChunkModel,
                SupportModel.id == SupportChunkModel.support_id,
            ).group_by(SupportModel.id).order_by(score_content.desc()).subquery()
        )

        score_dense_title = 1 - SupportModel.title_vector.cosine_distance(dense_vector)
        score_lexical_title = -1 * (
            SupportModel.title_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )
        score_title = ((score_lexical_title * lexical_ratio) + score_dense_title *
                       (1 - lexical_ratio)).label("score_title")

        rank_title = self.session.query(
            SupportModel.id,
            func.row_number().over(order_by=score_title.desc()).label("rank_title"),
        ).subquery()

        rrf_score = (1 / (rrf_k + rank_content.c.rank_content) + 1 /
                     (rrf_k + rank_title.c.rank_title)).label("rrf_score")

        query = (
            self.session.query(SupportModel).join(
                rank_content,
                SupportModel.id == rank_content.c.id,
            ).join(
                rank_title,
                SupportModel.id == rank_title.c.id,
            ).order_by(rrf_score.desc()).limit(k)
        )

        return query.all()

    def search_attachments_hybrid(
        self,
        dense_vector: Optional[List[float]] = None,
        sparse_vector: Optional[Dict[int, float]] = None,
        lexical_ratio: float = 0.5,
        k: int = 5,
        **kwargs,
    ):
        """내용으로 유사도 검색"""

        support_id = kwargs.get("support_id")
        if not support_id:
            raise ValueError()

        score_dense = 1 - SupportAttachmentContentModel.chunk_vector.max_inner_product(dense_vector)
        score_lexical = -1 * (
            SupportAttachmentContentModel.chunk_sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )

        score = func.max((score_lexical * lexical_ratio) + score_dense * (1 - lexical_ratio)).label("score")

        query = (
            self.session.query(SupportAttachmentContentModel).join(
                SupportAttachmentModel,
                SupportAttachmentModel.id == SupportAttachmentContentModel.attachment_id,
            ).join(
                SupportModel,
                SupportModel.id == SupportAttachmentModel.support_id,
            ).where(SupportModel.id == support_id).group_by(SupportChunkModel.id
                                                            ).group_by(SupportModel.id).order_by(score.desc()).limit(k)
        )

        return query.all()
