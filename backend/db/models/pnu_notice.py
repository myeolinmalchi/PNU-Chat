from dependency_injector import containers, providers

import db.repositories as repo

from services import notice, university


class PNUNoticeContainer(containers.DeclarativeContainer):
    semester_repo = providers.Dependency(repo.SemesterRepository)
    calendar_service = providers.Dependency(university.CalendarService)

    notice_repo = providers.Singleton(repo.PNUNoticeRepository)

    notice_service = providers.Factory(
        notice.PNUNoticeSearchServiceV1,
        notice_repo=notice_repo,
        calendar_service=calendar_service,
        semester_repo=semester_repo,
    )
