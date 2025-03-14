from typing import NotRequired, Optional, Required, TypedDict, List

from services.base import EmbedResult
from services.base.dto import BaseDTO


class AttachmentDTO(TypedDict):
    name: str
    url: str
    content: NotRequired[str | List[str]]


class NoticeInfoDTO(TypedDict):
    title: str
    content: str
    category: NotRequired[str]
    department: NotRequired[str]
    date: str
    author: str


class NoticeEmbeddingsDTO(TypedDict):
    title_embeddings: EmbedResult
    content_embeddings: EmbedResult | List[EmbedResult]
    attachment_embeddings: List[EmbedResult]


class NoticeDTO(BaseDTO, total=False):
    info: Required[NoticeInfoDTO]
    attachments: Required[List[AttachmentDTO]]
    embeddings: NoticeEmbeddingsDTO
