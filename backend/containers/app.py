from dependency_injector import containers, providers
from openai import AsyncOpenAI

from services.app import AppSearchService, ApplicationService

from .notice import NoticeContainer, PNUNoticeContainer
from .calendar import CalendarContainer
from .support import SupportContainer
from .professor import ProfessorContainer
from .university import UniversityContainer
from .agent import AssistantContainer

from db import repositories as repo


class AppContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[
        "app.api.chat_v3",
        "app.api.university",
    ])

    config = providers.Configuration(json_files=["config/config.json"])

    openai_client = providers.Singleton(AsyncOpenAI)

    univ_repo = providers.Singleton(repo.UniversityRepository)
    semester_repo = providers.Singleton(repo.SemesterRepository)
    calendar_repo = providers.Singleton(repo.CalendarRepository)

    calendar_package = providers.Container(
        CalendarContainer,
        calendar_repo=calendar_repo,
        semester_repo=semester_repo,
    )

    notice_package = providers.Container(
        NoticeContainer,
        semester_repo=semester_repo,
        univ_repo=univ_repo,
        calendar_service=calendar_package.calendar_service
    )

    pnu_notice_package = providers.Container(
        PNUNoticeContainer,
        semester_repo=semester_repo,
        calendar_service=calendar_package.calendar_service,
    )

    support_package = providers.Container(SupportContainer)
    professor_package = providers.Container(ProfessorContainer, univ_repo=univ_repo)
    univ_package = providers.Container(UniversityContainer, univ_repo=univ_repo)

    search_service = providers.Factory(
        AppSearchService,
        professor_service=professor_package.professor_service,
        notice_service=notice_package.notice_service,
        pnu_notice_service=pnu_notice_package.notice_service,
        calendar_service=calendar_package.calendar_service,
        support_service=support_package.support_service,
        univ_service=univ_package.univ_service,
        semester_repo=semester_repo
    )

    assistant_package = providers.Container(
        AssistantContainer,
        search_service=search_service,
        openai_client=openai_client,
        model=config.openai.model,
        temperature=config.openai.temperature,
    )

    app = providers.Factory(
        ApplicationService,
        professor_service=professor_package.professor_service,
        notice_service=notice_package.notice_service,
        calendar_service=calendar_package.calendar_service,
        support_service=support_package.support_service,
        univ_service=univ_package.univ_service,
        semester_repo=semester_repo
    )
