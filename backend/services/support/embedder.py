import asyncio
from itertools import chain

from services.base import BaseEmbedder
from services.base.embedder import embed_async
from services.support.dto import SupportDTO


class SupportEmbedder(BaseEmbedder[SupportDTO]):

    async def _embed_dtos_async(self, dtos, session, **kwargs):
        infos = [support["info"] for support in dtos]

        embed = lambda data: embed_async(
            texts=data if isinstance(data, list) else [data],
            session=session,
            chunking=False,
        )

        titles_future = embed([info["title"] for info in infos])

        contents = [info["content"] for info in infos]
        contents_future = asyncio.gather(*[embed(content) for content in contents])

        attachments = [support["attachments"] for support in dtos]
        attachments = [[att["content"] for att in atts if "content" in att] for atts in attachments]
        attachments_future = asyncio.gather(*[asyncio.gather(*[embed(att) for att in atts]) for atts in attachments])

        embeddings = await asyncio.gather(
            titles_future,
            contents_future,
            attachments_future,
        )

        embedding_dtos = [{
            "title_embeddings": te,
            "content_embeddings": ce,
            "attachment_embeddings": list(chain(*ae))
        } for te, ce, ae in zip(*embeddings)]

        return [SupportDTO(**{
            **dto,
            "embeddings": embeddings,
        }) for dto, embeddings in zip(dtos, embedding_dtos)]
