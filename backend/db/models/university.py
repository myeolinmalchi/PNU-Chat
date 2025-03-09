from typing import List
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, relationship, mapped_column
from db.common import Base, SQLEnum
from enum import Enum


class StructEnum(Enum):
    """구분(건물 구조)"""
    steel = "ST"
    light_steel = "경량ST"
    steel_reinforced_concrete = "SRC"
    reinforced_concrete = "RC"
    masonry = "석조"
    brick = "벽돌조"


class PlaceEnum(Enum):
    """구분(구내/외)"""
    onsite = "구내"
    offsite = "구외"


class SafetyEnum(Enum):
    """안전등급"""
    A = "A"
    B = "B"
    C = "C"


department_building_association = Table(
    "department_building_association", Base.metadata,
    Column("department_id", Integer, ForeignKey("departments.id"), primary_key=True),
    Column("building_num", Integer, ForeignKey("buildings.id"), primary_key=True)
)


class UniversityModel(Base):
    """단과대학 테이블"""

    __tablename__ = "universities"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    departments = relationship(
        "DepartmentModel",
        back_populates="university",
        lazy="joined",
    )


class DepartmentModel(Base):
    """학과 테이블"""

    __tablename__ = "departments"

    university_id = mapped_column(ForeignKey("universities.id"))
    name = mapped_column(String, nullable=False)
    university = relationship("UniversityModel", back_populates="departments", lazy="joined")

    majors: Mapped[List["MajorModel"]] = relationship("MajorModel", back_populates="department")
    professors = relationship("ProfessorModel", back_populates="department")
    notices = relationship("NoticeModel", back_populates="department")
    subjects = relationship("SubjectModel", back_populates="department")

    buildings: Mapped[List["BuildingModel"]] = relationship(
        secondary=department_building_association,
        back_populates="departments",
    )


class MajorModel(Base):
    """세부 전공 테이블"""

    __tablename__ = "majors"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    department_id = mapped_column(ForeignKey("departments.id"))

    department = relationship("DepartmentModel", back_populates="majors")
    professors = relationship("ProfessorModel", back_populates="major")


class BuildingModel(Base):
    """대학 건물 테이블"""

    __tablename__ = "buildings"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    building_num: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    place = mapped_column(SQLEnum(PlaceEnum), nullable=True)
    structure = mapped_column(SQLEnum(StructEnum), nullable=True)
    floor_under = mapped_column(Integer, nullable=True)
    floor_above = mapped_column(Integer, nullable=True)
    completion = mapped_column(String, nullable=True)
    building_area = mapped_column(Integer, nullable=True)
    total_floor_area = mapped_column(Integer, nullable=True)
    year_elapsed = mapped_column(Integer, nullable=True)
    safety = mapped_column(SQLEnum(SafetyEnum), nullable=True)

    longitude = mapped_column(Float, nullable=True)
    latitude = mapped_column(Float, nullable=True)

    timetables = relationship("CourseTimeTableModel", back_populates="building")
    departments: Mapped[List[DepartmentModel]] = relationship(
        secondary=department_building_association,
        back_populates="buildings",
    )
