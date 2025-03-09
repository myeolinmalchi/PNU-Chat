from dependency_injector import containers, providers

import db.repositories as repo
from services import notice


class NoticeCrawlerContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    univ_repo = providers.Singleton(repo.UniversityRepository)
    semester_repo = providers.Singleton(repo.SemesterRepository)

    notice_repo = providers.Singleton(repo.NoticeRepository)
    notice_embedder = providers.Singleton(notice.NoticeEmbedder)
    notice_crawler = providers.Singleton(notice.NoticeCrawler)

    notice_service = providers.Factory(
        notice.NoticeCrawlerService,
        notice_repo=notice_repo,
        notice_embedder=notice_embedder,
        notice_crawler=notice_crawler,
        university_repo=univ_repo,
        semester_repo=semester_repo,
    )
