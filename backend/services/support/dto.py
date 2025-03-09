from typing import NotRequired, Required, TypedDict, List

from services.base.dto import BaseDTO
from services.base.embedder import EmbedResult


class SupportAttachmentDTO(TypedDict):
    name: str
    url: str
    content: NotRequired[str | List[str]]


class SupportInfoDTO(TypedDict):
    category: str
    sub_category: str

    title: str
    content: str | List[str]


class SupportEmbeddingsDTO(TypedDict):
    title_embeddings: EmbedResult
    content_embeddings: List[EmbedResult]
    attachment_embeddings: List[EmbedResult]


class SupportDTO(BaseDTO, total=False):
    info: Required[SupportInfoDTO]
    embeddings: SupportEmbeddingsDTO
    attachments: Required[List[SupportAttachmentDTO]]
