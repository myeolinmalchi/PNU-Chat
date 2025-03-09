from config.config import get_universities
from db.models.universities import DepartmentModel, UniversityModel
from db.repositories.base import transaction
from db.repositories.university import UniversityRepository


@transaction()
def run():
    models = []

    univs = get_universities()

    for university, departments in univs.items():

        departments = [
            DepartmentModel(name=department) for department in departments
        ]

        model = UniversityModel(name=university, departments=departments)
        models.append(model)

    repo = UniversityRepository()
    repo.create_all(models)


if __name__ == "__main__":
    run()
