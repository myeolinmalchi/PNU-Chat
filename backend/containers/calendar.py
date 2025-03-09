from dependency_injector import containers, providers

import db.repositories as repo
from services import university


class CalendarContainer(containers.DeclarativeContainer):

    calendar_repo = providers.Dependency(repo.CalendarRepository)
    semester_repo = providers.Dependency(repo.SemesterRepository)

    calendar_service = providers.Factory(
        university.CalendarService,
        calendar_repo=calendar_repo,
        semester_repo=semester_repo,
    )
