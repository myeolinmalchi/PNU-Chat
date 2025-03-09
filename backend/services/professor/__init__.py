from typing import Literal
from .dto import *
from .service import *
from .embedder import *
from .crawler import *


def create_professor_service(_type: Literal["default", "me"] = "default"):
    match _type:
        case "default":
            Crawler = ProfessorCrawler
        case "me":
            Crawler = ProfessorMECrawler

    professor_repo = ProfessorRepository()
    professor_crawler = Crawler()
    professor_embedder = ProfessorEmbedder()
    univ_repo = UniversityRepository()

    professor_service = ProfessorService(
        professor_repo, professor_embedder, professor_crawler, univ_repo
    )

    return professor_service
