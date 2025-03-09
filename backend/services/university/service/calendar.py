from functools import lru_cache
from typing import List, Optional, Tuple
from db.models.calendar import CalendarModel, SemesterModel, SemesterTypeEnum
from db.repositories.base import transaction
from db.repositories.calendar import CalendarRepository, SemesterRepository
from services.base.service import BaseDomainService
from services.base.types.calendar import SemesterType
from services.university.dto import CalendarDTO
from datetime import datetime

CALENDAR_CONTEXT_TEMPLATE = """<Schedule>
    <period>
        <start>{}</start>
        <end>{}</end>
    </period>
    <description>{}</description>
<Schedule>"""


class CalendarService(BaseDomainService[CalendarDTO, CalendarModel]):

    def __init__(
        self,
        semester_repo: SemesterRepository,
        calendar_repo: CalendarRepository,
    ):
        self.semester_repo = semester_repo
        self.calendar_repo = calendar_repo

    @transaction()
    def dto2orm(self, dto):
        semester = dto["semester"]
        semester_model = self.semester_repo.search_semester_by_dto(semester)
        if not semester_model:
            raise ValueError("학기 정보가 존재하지 않습니다.")

        assert isinstance(semester_model, SemesterModel)

        CalendarModel(
            st_date=dto["date_range"]["st_date"],
            ed_date=dto["date_range"]["ed_date"],
            semester_id=semester_model.id,
            name=dto["description"]
        )
        return None

    @transaction()
    def orm2dto(self, orm):
        return CalendarDTO(
            **{
                "date_range": {
                    "st_date": orm.st_date,
                    "ed_date": orm.ed_date,
                },
                "description": orm.name,
                "semester": {
                    "year": orm.semester.year,
                    "type_": orm.semester.type_,
                }
            }
        )

    def dto2context(self, dto: CalendarDTO):
        return CALENDAR_CONTEXT_TEMPLATE.format(
            dto["date_range"]["st_date"],
            dto["date_range"]["ed_date"],
            dto["description"],
        )

    def get_related_semester(self, orm: SemesterModel) -> Optional[SemesterModel]:

        semester = None

        match orm:
            case SemesterModel(type_=SemesterTypeEnum.spring_semester):
                semester = self.semester_repo.search_semester_by_dto({
                    "year": orm.year - 1,
                    "type_": SemesterTypeEnum.winter_vacation
                })
            case SemesterModel(type_=SemesterTypeEnum.fall_semester):
                semester = self.semester_repo.search_semester_by_dto({
                    "year": orm.year,
                    "type_": SemesterTypeEnum.summer_vacation
                })
            case SemesterModel(type_=SemesterTypeEnum.summer_vacation):
                semester = self.semester_repo.search_semester_by_dto({
                    "year": orm.year,
                    "type_": SemesterTypeEnum.summer_vacation
                })
            case SemesterModel(type_=SemesterTypeEnum.winter_vacation):
                semester = self.semester_repo.search_semester_by_dto({
                    "year": orm.year + 1,
                    "type_": SemesterTypeEnum.summer_vacation
                })

        return semester

    def semester2dto(self, orm: SemesterModel):
        return SemesterType(
            semester_id=orm.id,
            year=orm.year,
            type_=orm.type_,
            period={
                "st_date": orm.st_date,
                "ed_date": orm.ed_date
            },
        )

    @lru_cache
    def get_semester(self, year: int, month: int, day: int) -> List[SemesterType]:

        with transaction():
            now = datetime(year, month, day)
            curr_semester = self.semester_repo.search_semester_by_date(now)

            if not curr_semester:
                raise ValueError

            assert not isinstance(curr_semester, list)

            semester = self.get_related_semester(curr_semester)

            if not semester:
                raise ValueError("학기 정보를 불러오지 못했습니다.")

            curr_semester_dto = self.semester2dto(curr_semester)
            semester_dto = self.semester2dto(semester)

            return [curr_semester_dto, semester_dto]

    @transaction()
    def search_calendars(self, semesters: List[SemesterType] | None = None):

        if not semesters:
            now = datetime.now()
            semesters = self.get_semester(now.year, now.month, now.day)
            ids = [s["semester_id"] for s in semesters if "semester_id" in s]
        else:
            semester_models = self.semester_repo.search_semester_by_dtos(semesters)
            ids = [s.id for s in semester_models]

        search_results = self.calendar_repo.search_calendars_by_semester_ids(ids)
        return [self.orm2dto(orm) for orm in search_results]
