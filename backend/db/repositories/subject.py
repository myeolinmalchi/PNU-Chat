from db.models.subject import CourseModel, SubjectModel
from db.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[SubjectModel]):
    pass


class CourseRepository(BaseRepository[CourseModel]):
    pass
