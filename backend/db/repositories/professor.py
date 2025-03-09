from typing import List, Dict

from pgvector.sqlalchemy import SparseVector
from sqlalchemy import and_, func
from db.common import V_DIM
from db.models import ProfessorModel, DepartmentModel
from db.models.professor import ProfessorDetailChunkModel
from db.repositories.base import BaseRepository


class ProfessorRepository(BaseRepository[ProfessorModel]):

    def create_all(self, objects):
        professors = []
        for professor in objects:
            professor_model = self.session.query(ProfessorModel).filter(
                ProfessorModel.url == professor.url
            ).first()

            if not professor_model:
                professors.append(professor)
                continue

        professors = super().create_all(professors)

        return professors

    def find(self, **kwargs):
        department_model: DepartmentModel | None = kwargs.get(
            "department", None
        )
        name: str | None = kwargs.get("name", None)

        filters = []
        if department_model:
            filter = ProfessorModel.department_id == department_model.id
            filters.append(filter)

        if name:
            filter = ProfessorModel.name.contains(name)
            filters.append(filter)

        filter = and_(*filters)

        return self.session.query(ProfessorModel).filter(filter).all()

    def delete_by_department(self, department: str):
        department_model = self.session.query(DepartmentModel).filter(
            DepartmentModel.name == department
        ).one_or_none()

        if department_model is None:
            raise ValueError(f"존재하지 않는 학과입니다: {department}")

        affected = self.session.query(ProfessorModel).filter(
            ProfessorModel.department_id == department_model.id
        ).delete()

        return affected

    def search_professors_hybrid(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[int, float],
        lexical_ratio: float = 0.5,
        k: int = 5,
    ):
        """내용으로 유사도 검색"""
        score_dense = 1 - ProfessorDetailChunkModel.dense_vector.max_inner_product(
            dense_vector
        )
        score_lexical = -1 * (
            ProfessorDetailChunkModel.sparse_vector.max_inner_product(
                SparseVector(sparse_vector, V_DIM)
            )
        )

        score = func.max((score_lexical * lexical_ratio) + score_dense *
                         (1 - lexical_ratio)).label("score")

        query = (
            self.session.query(ProfessorModel, score).join(
                ProfessorDetailChunkModel,
                ProfessorModel.id == ProfessorDetailChunkModel.professor_id
            ).group_by(ProfessorModel.id).order_by(score.desc()).limit(k)
        )

        return query.all()
