from datetime import date, datetime
from typing import List, Union

from sqlalchemy import and_, or_
from db.models import CalendarModel, SemesterModel
from db.repositories.base import BaseRepository

from services.base.types import SemesterType


class SemesterRepository(BaseRepository[SemesterModel]):

    def upsert_all(self, objects):

        updated = []
        for s in objects:
            filter = and_(SemesterModel.year == s.year, SemesterModel.type_ == s.type_)
            query = self.session.query(SemesterModel).filter(filter)
            s_ = self.upsert(s, query, ["st_date", "ed_date"])

            updated.append(s_)

        return updated

    def search_semester_by_date(self, date: date | datetime):
        date_str = date.strftime('%Y-%m-%d')
        filter = and_(SemesterModel.st_date <= date_str, SemesterModel.ed_date >= date_str)
        semester = self.session.query(SemesterModel).filter(filter).one_or_none()
        return semester

    def search_semester_by_dto(self, dto: SemesterType):
        filter = and_(SemesterModel.year == dto["year"], SemesterModel.type_ == dto["type_"])
        return self.session.query(SemesterModel).filter(filter).one_or_none()

    def search_semester_by_dtos(self, dtos: List[SemesterType]):
        filters = []
        for s in dtos:
            filter = and_(SemesterModel.year == s["year"], SemesterModel.type_ == s["type_"])
            filters.append(filter)

        filter = or_(*filters)
        semesters = self.session.query(SemesterModel).filter(filter).all()

        return semesters


class CalendarRepository(BaseRepository[CalendarModel]):

    def search_calendars_by_semester_ids(self, ids: Union[int, List[int]]):
        """학기 id로 학사 일정 검색"""

        if isinstance(ids, int):
            ids = [ids]

        query = (
            self.session.query(CalendarModel).join(SemesterModel, SemesterModel.id == CalendarModel.semester_id).filter(
                SemesterModel.id.in_(ids)
            )
        )

        return query.all()

    def search_calendars_by_semesters(self, semesters: Union[SemesterType, List[SemesterType]]):
        """년도 및 학기 종류 데이터로 학사 일정 검색"""

        filters = []
        for s in semesters:
            if isinstance(s, dict):
                filters.append(SemesterModel.year == s["year"])
                filters.append(SemesterModel.type_ == s["type_"])
            else:
                filters.append(SemesterModel.id == s)

        filter = or_(*filters)

        query = (
            self.session.query(CalendarModel).join(SemesterModel,
                                                   SemesterModel.id == CalendarModel.semester_id).filter(filter)
        )

        return query.all()
