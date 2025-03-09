from functools import lru_cache
from typing import Dict, List
from db.models.university import DepartmentModel, UniversityModel
from db.repositories.base import transaction
from db.repositories.university import UniversityRepository
from services.base.service import BaseDomainService
from services.university.dto import DepartmentDTO, UniversityDTO


class DepartmentService(BaseDomainService[DepartmentDTO, DepartmentModel]):

    def orm2dto(self, orm):
        return DepartmentDTO(**{"name": orm.name})

    def dto2orm(self, dto):
        return DepartmentModel(name=dto["name"])


class UniversityService(BaseDomainService[UniversityDTO, UniversityModel]):

    def __init__(
        self,
        univ_repo: UniversityRepository,
        department_service: DepartmentService,
    ):
        self.univ_repo = univ_repo
        self.department_service = department_service

    def orm2dto(self, orm):
        departments = [self.department_service.orm2dto(deps) for deps in orm.departments]
        return UniversityDTO(**{"name": orm.name, "departments": departments})

    def dto2orm(self, dto):
        return UniversityModel(name=dto["name"])

    @lru_cache
    @transaction()
    def search_all_departments(self):
        univs = self.univ_repo.find_all()

        univ_map: Dict[str, List[str]] = {univ.name: [deps.name for deps in univ.departments] for univ in univs}

        return univ_map

    @lru_cache
    @transaction()
    def search_all_universities(self):
        univs = self.univ_repo.find_all()
        dtos = [self.orm2dto(orm) for orm in univs]

        return dtos
