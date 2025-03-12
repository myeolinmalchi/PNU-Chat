from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.common import Base, SQLEnum
from enum import Enum


class SemesterTypeEnum(Enum):
    """학기 구분 ENUM

    "여름 계절학기", "겨울 계절학기", "미분류" -> DB에는 있지만 사용하지 않음.
    """
    spring_semester = "1학기"
    fall_semester = "2학기"
    summer_vacation = "여름방학"
    winter_vacation = "겨울방학"

    #summer_session = "여름 계절학기"
    #winter_session = "겨울 계절학기"
    #unassigned = "미분류"


class SemesterModel(Base):
    """학기 테이블

    Attributes:
        year: 학년도 (ex: 2023)
        type_: 학기 구분 (1학기/2학기/여름계절학기/겨울계절학기/미분류)
        st_date: 학기 시작 날짜
        ed_date: 학기 종료 날

        calendars: 학기 일정
        courses: 개설 강좌
    """

    __tablename__ = "semesters"

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    type_ = mapped_column(
        SQLEnum(SemesterTypeEnum),
        nullable=False,
        name="type",
    )

    st_date: Mapped[date] = mapped_column(Date, nullable=False)
    ed_date: Mapped[date] = mapped_column(Date, nullable=False)

    calendars = relationship("CalendarModel", back_populates="semester")
    courses = relationship("CourseModel", back_populates="semester")

    notices = relationship("NoticeModel", back_populates="semester")
    pnu_notices = relationship("PNUNoticeModel", back_populates="semester")


class CalendarModel(Base):
    """학사 일정 테이블
    
    Attributes:
        st_date: 일정 시작 날짜
        ed_date: 일정 종료 날짜

        type_: 일정 구분
        name: 일정 이름
        detail: 일정 상세

        semester_id: 학기 ID
    """

    __tablename__ = "calendars"

    st_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ed_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    type_: Mapped[Optional[str]] = mapped_column("type", String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(String, nullable=True)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=True)
    semester = relationship("SemesterModel", back_populates="calendars")
