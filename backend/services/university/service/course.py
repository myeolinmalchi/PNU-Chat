from typing import Dict, Tuple
from sqlalchemy.dialects.postgresql import Any
from db.models.subject import CourseModel, CourseTimeTableModel, SubjectModel
from db.models.university import DepartmentModel
from db.repositories.base import transaction
from db.repositories.professor import ProfessorRepository
from db.repositories.subject import CourseRepository, SubjectRepository
from db.repositories.university import UniversityRepository
from services.base.service import BaseDomainService, BaseService

from datetime import datetime, timedelta
import re
import pandas as pd


class CourseService():

    def __init__(
        self, professor_repo: ProfessorRepository, subject_repo: SubjectRepository, univ_repo: UniversityRepository,
        course_repo: CourseRepository
    ):
        self.professor_repo = professor_repo
        self.univ_repo = univ_repo
        self.subject_repo = subject_repo
        self.course_repo = course_repo

    def parse_time(self, time_str: str):
        time_ = time_str.split("-")
        if len(time_) == 2:
            st_str, ed_str = time_
            st_time = datetime.strptime(st_str, "%H:%M").time()
            ed_time = datetime.strptime(ed_str, "%H:%M").time()
        else:
            time_str = time_[0]

            delta_str, = re.findall(r'\((.*?)\)', time_str)
            delta = timedelta(minutes=int(delta_str))

            st_str = time_str.replace(f"({delta_str})", "")
            st_date = datetime.strptime(st_str, "%H:%M")

            ed_time = (st_date + delta).time()
            st_time = st_date.time()

        return st_time, ed_time

    def parse_classroom(self, raw: str):
        building, classroom = raw.split("-", 1)
        return {"building": building, "classroom": classroom}

    def parse_timetable(self, timetable_str: str):
        infos = timetable_str.split(" ")

        if not len(infos) == 3:
            return None

        weekday, time_str, classroom = infos
        st_time, ed_time = self.parse_time(time_str)

        return {"weekday": weekday, "st_time": st_time, "ed_time": ed_time, **self.parse_classroom(classroom)}

    def parse_timetables(self, raw: str):

        timetable_strs = raw.split(",<br/> ")
        timetable_dicts = [self.parse_timetable(t) for t in timetable_strs]

        return timetable_dicts

    def parse_subject(self, raw: str):
        subject_name = raw.split("/")[0]
        return subject_name

    def parse_department(self, raw: str):
        department_name = raw.split("<br/>")[0]
        return department_name

    def parse_professor(self, raw: str):
        if " 외 " in raw:
            professor_name = raw.split(" 외 ")[0]
            return professor_name

        return raw

    def parse_type(self, raw: str):
        if len(raw) == 4:
            return raw[:2] + " " + raw[2:]

        return None

    def subject2orm(self, dto: Dict):
        return SubjectModel(
            **({
                "department_id": dto["department_id"]
            } if dto["department_id"] != -1 else {}),
            code=dto["subject_code"],
            name=dto["subject_name"],
            level=dto["level"],
            type_=dto["type_"],
            grade=dto["grade"],
        )

    def timetable2orm(self, dto: Dict):
        return CourseTimeTableModel(
            day_of_week=dto["weekday"],
            st_time=dto["st_time"],
            ed_time=dto["ed_time"],
        )

    def course2orm(self, dto: Dict):
        return CourseModel(
            **({
                "professor_id": dto["professor_id"]
            } if dto["professor_id"] != -1 else {}),
            group=dto["group"],
            is_online=dto["is_online"],
            is_english=dto["is_english"],
            credit=dto["credit"],
            note=dto["note"]
        )

    @transaction()
    def preprocess(self, row: pd.Series, cache_dict: Dict[Tuple[str, str], Tuple[int, int]]):

        row_dict = {
            "subject_name": self.parse_subject(str(row["교과목명"])),
            "subject_code": str(row["교과목번호"]),
            "type_": self.parse_type(str(row["교과목구분"])),
            "grade": str(row["학년"]),
            "is_online": row["사이버강좌"],
            "is_english": row.notna()["원어강의"],
            "group": row["분반"],
            "credit": int(row["학점"]),
            "level": "대학",
            "note": str(row["비고"]),
            "timetables": self.parse_timetables(str(row["시간표"]))
        }

        department = self.parse_department(str(row["개설학과"]))
        professor_name = self.parse_professor(str(row["교수명"]))

        if (department, professor_name) in cache_dict:
            department_id, professor_id = cache_dict[(department, professor_name)]
            return pd.Series({**row_dict, "department_id": department_id, "professor_id": professor_id})

        department_model = self.univ_repo.find_department_by_name(department)

        if not department_model:
            cache_dict[(department, professor_name)] = (-1, -1)
            return pd.Series({**row_dict, "professor_id": -1, "department_id": -1})

        assert type(department_model) is DepartmentModel
        department_id = department_model.id

        professor_model = self.professor_repo.find(department_id=department_id, name=professor_name)
        professor_id = -1 if len(professor_model) == 0 else professor_model[0].id
        cache_dict[(department, professor_name)] = (department_id, professor_id)

        return pd.Series({**row_dict, "department_id": department_id, "professor_id": professor_id})

    @transaction()
    def run(self):
        df = pd.read_csv("config/courses.csv")
        cache_dict: Dict[Tuple[str, str], Tuple[int, int]] = {}
        df = df.apply(lambda row: self.preprocess(row, cache_dict), axis=1)
        course_dicts = df.to_dict(orient="records") # type: ignore

        df = df.groupby(["subject_name", "subject_code", "department_id"], as_index=False).first()
        subject_dicts = df.to_dict(orient='records') # type: ignore
        subject_dicts = [self.subject2orm(s) for s in subject_dicts]
        subject_dicts = {(s.department_id, s.code): s for s in subject_dicts}
