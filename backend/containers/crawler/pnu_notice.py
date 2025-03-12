from dependency_injector import containers, providers

import db.repositories as repo
from services import notice


class PNUNoticeCrawlerContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    semester_repo = providers.Singleton(repo.SemesterRepository)

    notice_repo = providers.Singleton(repo.PNUNoticeRepository)
    notice_embedder = providers.Singleton(notice.NoticeEmbedder)
    notice_crawler = providers.Singleton(notice.PNUNoticeCrawler)

    notice_service = providers.Factory(
        notice.PNUNoticeCrawlerSerivce,
        notice_repo=notice_repo,
        notice_embedder=notice_embedder,
        notice_crawler=notice_crawler,
        semester_repo=semester_repo,
    )
