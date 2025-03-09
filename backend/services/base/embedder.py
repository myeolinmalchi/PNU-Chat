from abc import ABC, abstractmethod
from typing import Generic, List, Optional, overload

from aiohttp import ClientSession
import requests

from mixins.asyncio import retry_async, retry_sync
from mixins.http_client import HTTPMetaclass
from dotenv import load_dotenv
import os

from services.base.dto import DTO, EmbedResult, RerankResult

load_dotenv()

EMBED_URL = os.environ.get("EMBED_URL")
TEI_URL = os.environ.get("TEI_URL")


@overload
async def embed_async(
    texts: List[str],
    session: ClientSession,
    chunking: bool = True,
    truncate: bool = True,
) -> List[EmbedResult]:
    pass


@overload
async def embed_async(
    texts: str,
    session: ClientSession,
    chunking: bool = True,
    truncate: bool = True,
) -> EmbedResult:
    pass


@retry_async(delay=3)
async def embed_async(
    texts: str | List[str],
    session: ClientSession,
    chunking: bool = True,
    truncate: bool = True,
) -> EmbedResult | List[EmbedResult]:
    body = {"inputs": texts, "chunking": chunking, "truncate": truncate}
    async with session.post(f"{EMBED_URL}/embed", json=body) as res:
        if res.status == 200:
            data = await res.json()
            return data

        raise Exception("텍스트 임베딩에 실패했습니다.")


@retry_sync(delay=3)
def embed(
    texts: str | List[str],
    chunking: bool = True,
    truncate: bool = True,
):
    body = {"inputs": texts, "chunking": chunking, "truncate": truncate}
    res = requests.post(f"{EMBED_URL}/embed", json=body)
    if res.status_code == 200:
        return res.json()

    raise Exception


@retry_async(delay=3)
async def rerank_async(
    query: str,
    texts: List[str],
    session: ClientSession,
    truncate: bool = True,
    truncation_direction="Right",
) -> List[RerankResult]:
    if not texts:
        return []

    body = {
        "query": query,
        "texts": texts,
        "truncate": truncate,
        "truncation_direction": truncation_direction,
    }
    async with session.post(f"{TEI_URL}/rerank", json=body) as res:
        if res.status == 200:
            data = await res.json()
            return data

        raise Exception("Failed Reranking")


class BaseEmbedder(ABC, Generic[DTO], metaclass=HTTPMetaclass):

    async def embed_dtos_async(self, dtos: List[DTO], session: Optional[ClientSession] = None, **kwargs) -> List[DTO]:
        if not session or type(session) is not ClientSession:
            raise ValueError("'session' argument must be provided.")

        return await self._embed_dtos_async(dtos, session=session, **kwargs)

    @abstractmethod
    async def _embed_dtos_async(self, dtos: List[DTO], session: ClientSession, **kwargs) -> List[DTO]:
        pass

    async def embed_dtos_batch_async(self, dtos: List[DTO], batch_size: int = 30, **kwargs) -> List[DTO]:
        session = kwargs.get("session")
        if not isinstance(session, ClientSession):
            raise ValueError("'session' argument must be provided.")

        def parts(_list: List[DTO], n):
            for idx in range(0, len(_list), n):
                yield _list[idx:idx + n]

        parted_items = list(parts(dtos, batch_size))

        xss = [await self.embed_dtos_async(_items, session=session) for _items in parted_items]

        return [x for xs in xss for x in xs]
