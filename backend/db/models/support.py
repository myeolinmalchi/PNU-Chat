from typing import List, Optional
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from db.common import Base
from db.common import N_DIM, V_DIM
from pgvector.sqlalchemy import Vector, SPARSEVEC


class SupportModel(Base):
    """부산대 학지시"""

    __tablename__ = "supports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    sub_category: Mapped[str] = mapped_column(String, nullable=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    content: Mapped[str] = mapped_column(String, nullable=False)

    title_vector = mapped_column(Vector(dim=N_DIM), nullable=True)
    title_sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM), nullable=True)

    content_chunks: Mapped[List["SupportChunkModel"]] = relationship(back_populates="support", lazy="joined")
    attachments: Mapped[List["SupportAttachmentModel"]] = relationship(back_populates="support", lazy="joined")


class SupportAttachmentModel(Base):
    """학지시 각 항목 첨부파일 테이블"""

    __tablename__ = "support_attachments"

    support_id: Mapped[int] = mapped_column(ForeignKey("supports.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    support: Mapped["SupportModel"] = relationship("SupportModel", back_populates="attachments", lazy="joined")
    content_chunks: Mapped[List["SupportChunkModel"]] = relationship(back_populates="attachment", lazy="joined")


class SupportChunkModel(Base):
    """부산대 학지시 세부사항 chunk"""

    __tablename__ = "support_content_chunks"

    support_id: Mapped[int] = mapped_column(
        ForeignKey("supports.id", ondelete="CASCADE"),
        index=True,
    )

    attachment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("support_attachments.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    chunk_content: Mapped[str] = mapped_column(String, nullable=False)

    chunk_vector = mapped_column(Vector(dim=N_DIM), nullable=True)
    chunk_sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM), nullable=True)

    support: Mapped["SupportModel"] = relationship(
        back_populates="content_chunks",
        lazy="joined",
    )

    attachment: Mapped[Optional["SupportAttachmentModel"]] = relationship(
        back_populates="content_chunks",
        lazy="joined",
    )


"""
class SupportAttachmentContentModel(Base):

    __tablename__ = "support_attachment_contents"

    attachment_id: Mapped[int] = mapped_column(ForeignKey("support_attachments.id", ondelete="CASCADE"))

    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)

    chunk_vector = mapped_column(Vector(dim=N_DIM), nullable=True)
    chunk_sparse_vector = mapped_column(SPARSEVEC(dim=V_DIM), nullable=True)

    attachment: Mapped["SupportAttachmentModel"] = relationship(back_populates="contents", lazy="joined")
"""
