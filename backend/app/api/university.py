from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from containers.app import AppContainer
from services.university.service.university import UniversityService

router = APIRouter(prefix="/api")


@router.get("/universities")
@inject
async def chat(univ_service: UniversityService = Depends(Provide[AppContainer.univ_package.univ_service]), ):
    return univ_service.search_all_departments()
