import textwrap
from typing import Generic, Optional, TypeVar
from pgvector.sqlalchemy import SparseVector

from db.common import V_DIM

from db.models import AttachmentModel, NoticeChunkModel, NoticeModel, DepartmentModel
from db.models.notice import PNUNoticeAttachmentModel, PNUNoticeChunkModel, PNUNoticeModel

from db.repositories.notice import NoticeRepository, PNUNoticeRepository
from db.repositories.university import UniversityRepository

from db.repositories.calendar import SemesterRepository

from services.base import BaseDomainService
from services.notice import AttachmentDTO, NoticeDTO
from services.university import CalendarService

from itertools import chain

NoticeModelT = TypeVar("NoticeModelT", NoticeModel, PNUNoticeModel)


class BaseNoticeService(
    BaseDomainService[NoticeDTO, NoticeModelT],
    Generic[NoticeModelT],
):

    def __init__(
        self,
        semester_repo: SemesterRepository,
        notice_repo: NoticeRepository | PNUNoticeRepository,
        calendar_service: Optional[CalendarService] = None,
    ):
        self.semester_repo = semester_repo
        self.notice_repo = notice_repo
        self.calendar_service = calendar_service

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

        if not chunk_models:
            attachment_models = [AttachmentModel(
                name=att["name"],
                url=att["url"],
            ) for att in attachments]

        else:
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
                    {f'<department>{info["department"]}</department>' if "department" in info else ""}
                    {f'<category>{info["category"]}</category>' if "category" in info else ""}
                </metadata>
                {att_content}
                <content>
                    {info["content"]}
                </content>
            </Notice>
            """
        )


class BaseDepartmentNoticeService(BaseNoticeService[NoticeModel]):

    def __init__(self, university_repo: UniversityRepository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.university_repo = university_repo

    def orm2dto(self, orm, **_):
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

    def dto2orm(self, dto, **kwargs):
        is_important = kwargs.get("is_important", False)

        info = self._parse_info(dto)
        attachments = self._parse_attachments(dto)
        embeddings = self._parse_embeddings(dto)

        if not info or "department" not in info:
            return None

        department_model = self.university_repo.find_department_by_name(info["department"])

        if type(department_model) is not DepartmentModel:
            raise ValueError(f"[]")

        del info["department"]

        if is_important and info["title"].startswith("전체게시판공지"):
            del info["category"]

        notice_dict = {
            **info,
            "attachments": attachments["attachments"],
            "title_vector": embeddings["title_vector"],
            "title_sparse_vector": embeddings["title_sparse_vector"],
            "content_chunks": [*embeddings["content_chunks"], *attachments["content_chunks"]],
            "department_id": department_model.id,
            "url": dto["url"],
            "is_important": is_important,
        }

        return NoticeModel(**notice_dict)


class BasePNUNoticeService(BaseNoticeService[PNUNoticeModel]):

    def _parse_attachments(self, dto: NoticeDTO):

        attachments = dto.get("attachments")
        embeddings = dto.get("embeddings")

        if not embeddings or not attachments:
            return {"attachments": [], "content_chunks": []}

        chunk_models = [[
            PNUNoticeChunkModel(
                chunk_vector=embedding["dense"],
                chunk_sparse_vector=SparseVector(embedding["sparse"], V_DIM),
                chunk_content=content,
            ) for content in att["content"]
        ] for embedding, att in zip(embeddings["attachment_embeddings"], attachments) if "content" in att]

        attachment_models = [
            PNUNoticeAttachmentModel(name=att["name"], url=att["url"], content_chunks=chunks)
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
            PNUNoticeChunkModel(
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

    def orm2dto(self, orm, **_):

        attachments = [{"name": att.name, "url": att.url} for att in orm.attachments]
        info = {
            "title": orm.title,
            "content": orm.content,
            "category": orm.category,
            "date": str(orm.date),
            "author": orm.author
        }

        return NoticeDTO(**{"info": info, "attachments": attachments, "url": orm.url})

    def dto2orm(self, dto, **_):
        info = self._parse_info(dto)
        attachments = self._parse_attachments(dto)
        embeddings = self._parse_embeddings(dto)

        if not info:
            return None

        notice_dict = {
            **info,
            "attachments": attachments["attachments"],
            "title_vector": embeddings["title_vector"],
            "title_sparse_vector": embeddings["title_sparse_vector"],
            "content_chunks": [*embeddings["content_chunks"], *attachments["content_chunks"]],
            "url": dto["url"],
        }

        return PNUNoticeModel(**notice_dict)
