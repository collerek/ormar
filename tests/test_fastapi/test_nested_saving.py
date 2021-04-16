import json
from typing import Optional

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


class Student(ormar.Model):
    class Meta:
        database = database
        metadata = metadata

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    courses = ormar.ManyToMany(Course)


# create db and tables
@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


to_exclude = {
    "id": ...,
    "courses": {
        "__all__": {"id": ..., "students": {"__all__": {"id", "studentcourse"}}}
    },
}

exclude_all = {"id": ..., "courses": {"__all__"}}

to_exclude_ormar = {
    "id": ...,
    "courses": {"id": ..., "students": {"id", "studentcourse"}},
}


@app.post("/departments/", response_model=Department)
async def create_department(department: Department):
    await department.save_related(follow=True, save_all=True)
    return department


@app.get("/departments/{department_name}")
async def get_department(department_name: str):
    department = await Department.objects.select_all(follow=True).get(
        department_name=department_name
    )
    return department.dict(exclude=to_exclude)


@app.get("/departments/{department_name}/second")
async def get_department_exclude(department_name: str):
    department = await Department.objects.select_all(follow=True).get(
        department_name=department_name
    )
    return department.dict(exclude=to_exclude_ormar)


@app.get("/departments/{department_name}/exclude")
async def get_department_exclude_all(department_name: str):
    department = await Department.objects.select_all(follow=True).get(
        department_name=department_name
    )
    return department.dict(exclude=exclude_all)


def test_saving_related_in_fastapi():
    client = TestClient(app)
    with client as client:
        payload = {
            "department_name": "Ormar",
            "courses": [
                {
                    "course_name": "basic1",
                    "completed": True,
                    "students": [{"name": "Jack"}, {"name": "Abi"}],
                },
                {
                    "course_name": "basic2",
                    "completed": True,
                    "students": [{"name": "Kate"}, {"name": "Miranda"}],
                },
            ],
        }
        response = client.post("/departments/", data=json.dumps(payload))
        department = Department(**response.json())

        assert department.id is not None
        assert len(department.courses) == 2
        assert department.department_name == "Ormar"
        assert department.courses[0].course_name == "basic1"
        assert department.courses[0].completed
        assert department.courses[1].course_name == "basic2"
        assert department.courses[1].completed

        response = client.get("/departments/Ormar")
        response2 = client.get("/departments/Ormar/second")
        assert response.json() == response2.json() == payload

        response3 = client.get("/departments/Ormar/exclude")
        assert response3.json() == {"department_name": "Ormar"}
