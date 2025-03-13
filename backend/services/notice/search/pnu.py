from abc import abstractmethod
from datetime import datetime
from typing import Dict, List, NotRequired, Optional, TypedDict, Unpack
from aiohttp import ClientSession

from db.repositories.base import transaction
from db.repositories.notice import PNUNoticeRepository
from services.base import SemesterType
from services.base.embedder import embed_async
from services.notice import NoticeDTO

from typing import TypedDict
from services.notice.base import BasePNUNoticeService
from services.notice.dto import AttachmentDTO


class IPNUNoticeSearchService(BasePNUNoticeService):

    class _SearchOptions(TypedDict, total=False):
        top_k: NotRequired[int]
        count: NotRequired[int]
        threshold: NotRequired[float]
        lexical_ratio: NotRequired[float]
        semesters: NotRequired[List[SemesterType]]

    @abstractmethod
    async def search_notices_async(
        self,
        query: str,
        session: Optional[ClientSession] = None,
        **opts: Unpack[_SearchOptions],
    ) -> List[NoticeDTO]:
        pass


class PNUNoticeSearchServiceV1(IPNUNoticeSearchService):

    async def search_notices_async(self, query, session=None, **opts):
        """search without reranker"""

        if type(self.notice_repo) is not PNUNoticeRepository:
            raise ValueError

        if not session:
            raise ValueError("'session' must be provided")

        if not self.calendar_service:
            raise ValueError("'NoticeService.calendar_service' must be provided")

        embed_result = await embed_async(query, session=session, chunking=False)
        assert not isinstance(embed_result, list)

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
                k=opts.get("count", 5),
            )
            notice_dict: Dict[int, NoticeDTO] = {}

            for chunk in chunks:
                attachment_model = chunk.attachment
                notice_id = chunk.pnu_notice_id

                if notice_id not in notice_dict:
                    dto = self.orm2dto(chunk.pnu_notice)
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
