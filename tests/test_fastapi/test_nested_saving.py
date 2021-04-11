import json
from typing import List, Optional

import databases
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)
app.state.database = database


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


class Department(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    department_name: str = ormar.String(max_length=100)


class Course(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    course_name: str = ormar.String(max_length=100)
    completed: bool = ormar.Boolean()
    department: Optional[Department] = ormar.ForeignKey(Department)


# create db and tables
@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/DepartmentWithCourses/", response_model=Department)
async def create_department(department: Department):
    # there is no save all - you need to split into save and save_related
    await department.save()
    await department.save_related(follow=True, save_all=True)
    return department


@app.get("/DepartmentsAll/", response_model=List[Department])
async def get_Courses():
    # if you don't provide default name it related model name + s so courses not course
    departmentall = await Department.objects.select_related("courses").all()
    return departmentall


def test_saving_related_in_fastapi():
    client = TestClient(app)
    with client as client:
        payload = {
            "department_name": "Ormar",
            "courses": [
                {"course_name": "basic1", "completed": True},
                {"course_name": "basic2", "completed": True},
            ],
        }
        response = client.post("/DepartmentWithCourses/", data=json.dumps(payload))
        department = Department(**response.json())

        assert department.id is not None
        assert len(department.courses) == 2
        assert department.department_name == "Ormar"
        assert department.courses[0].course_name == "basic1"
        assert department.courses[0].completed
        assert department.courses[1].course_name == "basic2"
        assert department.courses[1].completed

        response = client.get("/DepartmentsAll/")
        departments = [Department(**x) for x in response.json()]
        assert departments[0].id is not None
        assert len(departments[0].courses) == 2
        assert departments[0].department_name == "Ormar"
        assert departments[0].courses[0].course_name == "basic1"
        assert departments[0].courses[0].completed
        assert departments[0].courses[1].course_name == "basic2"
        assert departments[0].courses[1].completed
