from itertools import cycle

from services.base import BaseEmbedder
from services.professor import ProfessorDTO


class ProfessorEmbedder(BaseEmbedder[ProfessorDTO]):

    async def _embed_dtos_async(self, items, session):
        _infos = [professor["info"] for professor in items]
        _details = [info["detail"] for info in _infos if "detail" in info]

        details, indicies = [], []
        for idx, p in enumerate(items):
            _info = p["info"]
            if "detail" in _info:
                details.append(_info["detail"])
                indicies.append(idx)

        embeddings = await self._embed_async(
            texts=_details, session=session, chunking=True
        )

        assert isinstance(embeddings, list)
        _embeddings = cycle(embeddings)

        return [
            ProfessorDTO(
                **professor,
                **({
                    "embeddings": next(_embeddings)
                } if idx in indicies else {})
            ) for idx, professor in enumerate(items)
        ]
