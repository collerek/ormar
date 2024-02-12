# type: ignore
from typing import ForwardRef, List, Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


TeacherRef = ForwardRef("Teacher")


class Student(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    primary_teacher: TeacherRef = ormar.ForeignKey(
        TeacherRef, related_name="own_students"
    )


class StudentTeacher(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="students_x_teachers")


class Teacher(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    students = ormar.ManyToMany(
        Student, through=StudentTeacher, related_name="teachers"
    )


Student.update_forward_refs()

CityRef = ForwardRef("City")
CountryRef = ForwardRef("Country")


class Country(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="countries")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128)
    capital: Optional[CityRef] = ormar.ForeignKey(
        CityRef, related_name="capital_city", nullable=True
    )
    borders: Optional[List[CountryRef]] = ormar.ManyToMany(CountryRef)


class City(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="cities")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=128)
    country: Country = ormar.ForeignKey(
        Country, related_name="cities", skip_reverse=True
    )


Country.update_forward_refs()


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_double_relations():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            t1 = await Teacher.objects.create(name="Mr. Jones")
            t2 = await Teacher.objects.create(name="Ms. Smith")
            t3 = await Teacher.objects.create(name="Mr. Quibble")

            s1 = await Student.objects.create(name="Joe", primary_teacher=t1)
            s2 = await Student.objects.create(name="Sam", primary_teacher=t1)
            s3 = await Student.objects.create(name="Kate", primary_teacher=t2)
            s4 = await Student.objects.create(name="Zoe", primary_teacher=t2)
            s5 = await Student.objects.create(name="John", primary_teacher=t3)
            s6 = await Student.objects.create(name="Anna", primary_teacher=t3)

            for t in [t1, t2, t3]:
                for s in [s1, s2, s3, s4, s5, s6]:
                    await t.students.add(s)

            jones = (
                await Teacher.objects.select_related(["students", "own_students"])
                .order_by(["students__name", "own_students__name"])
                .get(name="Mr. Jones")
            )
            assert len(jones.students) == 6
            assert jones.students[0].name == "Anna"
            assert jones.students[5].name == "Zoe"
            assert len(jones.own_students) == 2
            assert jones.own_students[0].name == "Joe"
            assert jones.own_students[1].name == "Sam"

            smith = (
                await Teacher.objects.select_related(["students", "own_students"])
                .filter(students__name__contains="a")
                .order_by(["students__name", "own_students__name"])
                .get(name="Ms. Smith")
            )
            assert len(smith.students) == 3
            assert smith.students[0].name == "Anna"
            assert smith.students[2].name == "Sam"
            assert len(smith.own_students) == 2
            assert smith.own_students[0].name == "Kate"
            assert smith.own_students[1].name == "Zoe"

            quibble = (
                await Teacher.objects.select_related(["students", "own_students"])
                .filter(students__name__startswith="J")
                .order_by(["-students__name", "own_students__name"])
                .get(name="Mr. Quibble")
            )
            assert len(quibble.students) == 2
            assert quibble.students[1].name == "Joe"
            assert quibble.students[0].name == "John"
            assert len(quibble.own_students) == 2
            assert quibble.own_students[1].name == "John"
            assert quibble.own_students[0].name == "Anna"


@pytest.mark.asyncio
async def test_auto_through_model():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            england = await Country(name="England").save()
            france = await Country(name="France").save()
            london = await City(name="London", country=england).save()
            england.capital = london
            await england.update()
            await england.borders.add(france)

            check = await Country.objects.select_related(["capital", "borders"]).get(
                name="England"
            )
            assert check.name == "England"
            assert check.capital.name == "London"
            assert check.capital.country.pk == check.pk
            assert check.borders[0] == france
