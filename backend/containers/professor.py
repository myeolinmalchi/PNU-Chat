from dependency_injector import containers, providers

import db.repositories as repo
from services import professor


class ProfessorContainer(containers.DeclarativeContainer):
    univ_repo = providers.Dependency(repo.UniversityRepository)

    professor_repo = providers.Singleton(repo.ProfessorRepository)
    professor_embedder = providers.Singleton(professor.ProfessorEmbedder)
    professor_crawler = providers.Singleton(professor.ProfessorEmbedder)

    professor_service = providers.Factory(
        professor.ProfessorService,
        professor_repo=professor_repo,
        professor_embedder=professor_embedder,
        professor_crawler=professor_crawler,
        univ_repo=univ_repo
    )
