from dependency_injector import containers, providers

import db.repositories as repo
from services import support


class SupportContainer(containers.DeclarativeContainer):

    support_repo = providers.Singleton(repo.SupportRepository)
    support_embedder = providers.Singleton(support.SupportEmbedder)
    support_crawler = providers.Singleton(support.SupportCrawler)

    support_service = providers.Factory(
        support.SupportServiceV1,
        support_repo=support_repo,
        support_embedder=support_embedder,
        support_crawler=support_crawler
    )
