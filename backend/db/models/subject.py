from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, relationship, mapped_column
from db.common import Base, SQLEnum
from enum import Enum


class GradeEnum(Enum):
    """학년 구분"""
    freshman = "1"
    sophormore = "2"
    junior = "3"
    senior = "4"


class LevelEnum(Enum):
    """학교 구분"""
    undergraduate = "대학"
    graduate = "대학원"


class SubjectTypeEnum(Enum):
    """교과목 구분"""
    general_required = "교양 필수"
    general_elective = "교양 선택"
    major_required = "전공 필수"
    major_elective = "전공 선택"
    major_basics = "전공 기초"
    teacher_education = "교직 과목"


# TODO:
# - 교육과정표 테이블 추가
# - 강의계획서 데이터 수집
class SubjectModel(Base):
    """교과목 테이블
    
    Attributes:
        department_id: 학과 ID
        name: 교과목 이름
        level: 개설 과정
        type_: 과목 구분
        grade: 학년 구분
        code: 교과목 코드

        departments: 학과
        courses: 개설 강좌
    """

    __tablename__ = "subjects"

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[LevelEnum] = mapped_column(SQLEnum(LevelEnum), default="학부")
    type_: Mapped[SubjectTypeEnum] = mapped_column(SQLEnum(SubjectTypeEnum), name="type", nullable=False)

    grade: Mapped[GradeEnum] = mapped_column(SQLEnum(GradeEnum), nullable=True)
    code: Mapped[str] = mapped_column(String, nullable=False)

    department = relationship("DepartmentModel", back_populates="subjects")
    courses = relationship("CourseModel", back_populates="subject")


class CourseModel(Base):
    """수강 편람 테이블

    Attributes:
        subject_id: 교과목 ID
        professor_id: 강사 ID
        semester_id: 학기 ID

        group: 분반
        is_online: 온라인 강의 여부
        is_english: 영어 강의 여부
        credit: 학점

        subject: 교과목
        professor: 강사
        semester: 학기
        timetables: 시간표
    """

    __tablename__ = "courses"

    subject_id = mapped_column(ForeignKey("subjects.id"))
    professor_id = mapped_column(ForeignKey("professors.id"))
    semester_id = mapped_column(ForeignKey("semesters.id"))

    group = mapped_column(Integer, nullable=False)
    is_online = mapped_column(String, nullable=True)
    is_english = mapped_column(Boolean, default=False)

    credit = mapped_column(Float, nullable=False)

    note: Mapped[str] = mapped_column(String, nullable=True)

    subject = relationship("SubjectModel", back_populates="courses")
    professor = relationship("ProfessorModel", back_populates="courses")
    semester = relationship("SemesterModel", back_populates="courses")

    timetables = relationship("CourseTimeTableModel", back_populates="course")


class WeekdayEnum(Enum):
    월 = "월"
    화 = "화"
    수 = "수"
    목 = "목"
    금 = "금"
    토 = "토"
    일 = "일"


class CourseTimeTableModel(Base):
    """상세 시간표 테이블

    Attributes:
        course_id: 강좌 ID
        day_of_week: 요일
        building_id: 건물 ID
        classroom: 강의실

        st_time: 시작 시간
        ed_time: 종료 시간
        
        is_remote: 원격 강의 여부
        
        course: 강좌
        building: 건물
    """

    __tablename__ = "timetables"

    course_id = mapped_column(ForeignKey("courses.id"))

    day_of_week = mapped_column(SQLEnum(WeekdayEnum), nullable=False)
    building_id = mapped_column(ForeignKey("buildings.id"), nullable=True)
    classroom = mapped_column(String, nullable=False)

    st_time = mapped_column(Time, nullable=True)
    ed_time = mapped_column(Time, nullable=True)

    is_remote = mapped_column(Boolean, default=False)

    course = relationship("CourseModel", back_populates="timetables")
    building = relationship("BuildingModel", back_populates="timetables")
