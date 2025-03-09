from dependency_injector import containers, providers

from db.repositories.university import UniversityRepository
from services.university.service.university import DepartmentService, UniversityService


class UniversityContainer(containers.DeclarativeContainer):

    univ_repo = providers.Dependency(UniversityRepository)
    department_service = providers.Singleton(DepartmentService)
    univ_service = providers.Factory(
        UniversityService,
        univ_repo=univ_repo,
        department_service=department_service,
    )
