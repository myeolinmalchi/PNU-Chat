from datetime import datetime
from sqlalchemy import Boolean, Date, ForeignKey, Index, String
from pgvector.sqlalchemy import Vector, SPARSEVEC
from sqlalchemy.orm import mapped_column, relationship, Mapped
from db.common import N_DIM, V_DIM, Base
from typing import List, Optional

from db.models.calendar import SemesterModel
from db.models.university import DepartmentModel


class NoticeModel(Base):
    """학과 공지사항 테이블"""

    __tablename__ = "notices"

    __table_args__ = (Index(
        'ix_notice_department_semester',
        'department_id',
        'semester_id',
    ), )

    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=True, index=True)

    category: Mapped[str] = mapped_column(String, nullable=False)

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=True)
    department: Mapped[DepartmentModel] = relationship(back_populates="notices", lazy="joined")

    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=True)

    title_vector = mapped_column(Vector(N_DIM), nullable=True)
    title_sparse_vector = mapped_column(SPARSEVEC(V_DIM), nullable=True)

    attachments: Mapped[List["AttachmentModel"]] = relationship(back_populates="notice", lazy="joined")
    content_chunks: Mapped[List["NoticeChunkModel"]] = relationship(back_populates="notice", lazy="joined")

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=True)
    semester: Mapped[SemesterModel] = relationship(back_populates="notices")


class AttachmentModel(Base):
    """게시글의 첨부파일 테이블"""

    __tablename__ = "notice_attachments"

    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    notice: Mapped["NoticeModel"] = relationship(back_populates="attachments")
    content_chunks: Mapped[List["NoticeChunkModel"]] = relationship(back_populates="attachment", lazy="joined")


class NoticeChunkModel(Base):
    """게시글 본문 또는 첨부파일 청크 테이블"""
    __tablename__ = "notice_content_chunks"

    notice_id: Mapped[int] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"),
        index=True,
    )

    attachment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("notice_attachments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    chunk_content: Mapped[str] = mapped_column(String, nullable=False)
    chunk_vector = mapped_column(Vector(N_DIM))
    chunk_sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM))

    notice: Mapped["NoticeModel"] = relationship(back_populates="content_chunks")
    attachment: Mapped[Optional["AttachmentModel"]] = relationship(back_populates="content_chunks")


class PNUNoticeModel(Base):
    __tablename__ = "pnu_notices"

    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=True, index=True)

    category: Mapped[str] = mapped_column(String, nullable=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=True)

    title_vector = mapped_column(Vector(N_DIM), nullable=True)
    title_sparse_vector = mapped_column(SPARSEVEC(V_DIM), nullable=True)

    attachments: Mapped[List["PNUNoticeAttachmentModel"]] = relationship(back_populates="pnu_notice", lazy="joined")
    content_chunks: Mapped[List["PNUNoticeChunkModel"]] = relationship(back_populates="pnu_notice", lazy="joined")

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=True)
    semester: Mapped[SemesterModel] = relationship(back_populates="pnu_notices")


class PNUNoticeAttachmentModel(Base):

    __tablename__ = "pnu_notice_attachments"

    pnu_notice_id: Mapped[int] = mapped_column(ForeignKey("pnu_notices.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    pnu_notice: Mapped["PNUNoticeModel"] = relationship(back_populates="attachments")
    content_chunks: Mapped[List["PNUNoticeChunkModel"]] = relationship(back_populates="attachment", lazy="joined")


class PNUNoticeChunkModel(Base):
    __tablename__ = "pnu_notice_content_chunks"

    pnu_notice_id: Mapped[int] = mapped_column(
        ForeignKey("pnu_notices.id", ondelete="CASCADE"),
        index=True,
    )

    attachment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pnu_notice_attachments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    chunk_content: Mapped[str] = mapped_column(String, nullable=False)
    chunk_vector = mapped_column(Vector(N_DIM))
    chunk_sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM))

    pnu_notice: Mapped["PNUNoticeModel"] = relationship(back_populates="content_chunks")
    attachment: Mapped[Optional["PNUNoticeAttachmentModel"]] = relationship(back_populates="content_chunks")
