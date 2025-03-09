from dependency_injector import containers, providers

import db.repositories as repo

from services import notice, university


class NoticeContainer(containers.DeclarativeContainer):
    univ_repo = providers.Dependency(repo.UniversityRepository)
    semester_repo = providers.Dependency(repo.SemesterRepository)
    calendar_service = providers.Dependency(university.CalendarService)

    notice_repo = providers.Singleton(repo.NoticeRepository)
    notice_embedder = providers.Singleton(notice.NoticeEmbedder)

    notice_service = providers.Factory(
        notice.NoticeServiceV1,
        notice_repo=notice_repo,
        notice_embedder=notice_embedder,
        calendar_service=calendar_service,
        university_repo=univ_repo,
        semester_repo=semester_repo,
    )
