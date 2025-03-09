from typing import List
from pgvector.sqlalchemy import SPARSEVEC, Vector
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from db.common import N_DIM, V_DIM, Base
from db.models.subject import CourseModel


class ProfessorModel(Base):
    """교수 테이블"""

    __tablename__ = "professors"

    url = mapped_column(String, nullable=False, unique=True)

    department_id = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )
    major_id = mapped_column(ForeignKey("majors.id"), nullable=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    name_eng: Mapped[str] = mapped_column(String, nullable=True)

    profile_img: Mapped[str] = mapped_column(String, nullable=True)
    office_phone: Mapped[str] = mapped_column(String, nullable=True)
    website: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    lab_addr: Mapped[str] = mapped_column(String, nullable=True)

    department = relationship("DepartmentModel", back_populates="professors")
    major = relationship("MajorModel", back_populates="professors")

    detail: Mapped[str] = mapped_column(String, nullable=True)
    detail_chunks: Mapped[List["ProfessorDetailChunkModel"]
                          ] = relationship(back_populates="professor")

    courses: Mapped[List["CourseModel"]
                    ] = relationship(back_populates="professor")


class ProfessorDetailChunkModel(Base):
    """교수 상세 정보 청크 테이블"""
    __tablename__ = "professor_detail_chunks"

    professor_id = mapped_column(
        ForeignKey("professors.id", ondelete="CASCADE"), index=True
    )

    detail = mapped_column(String, nullable=False)
    dense_vector = mapped_column(Vector(N_DIM))
    sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM))

    professor: Mapped[ProfessorModel] = relationship(
        back_populates="detail_chunks"
    )
