from typing import List
from dependency_injector.wiring import Provide, inject
from containers.crawler.notice import NoticeCrawlerContainer
from db.models.calendar import SemesterTypeEnum
from services.base.types.calendar import SemesterType
from services.notice.crawler.base import BaseNoticeCrawlerService


@inject
def run(service: BaseNoticeCrawlerService = Provide[NoticeCrawlerContainer.notice_service]):
    years = [2023, 2024, 2025]
    types: List[SemesterTypeEnum] = [
        SemesterTypeEnum.spring_semester,
        SemesterTypeEnum.summer_vacation,
        SemesterTypeEnum.fall_semester,
        SemesterTypeEnum.winter_vacation,
    ]
    semesters = [SemesterType(year=year, type_=type_) for year in years for type_ in types]
    affected = service.add_semester_info(semesters)
    print("affected: ", affected)


if __name__ == "__main__":
    notice_container = NoticeCrawlerContainer()
    notice_container.init_resources()
    notice_container.wire(modules=[__name__])

    run()
