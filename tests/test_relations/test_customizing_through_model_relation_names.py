import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class Course(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    course_name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    courses = ormar.ManyToMany(
        Course,
        through_relation_name="student_id",
        through_reverse_relation_name="course_id",
    )


create_test_database = init_tests(base_ormar_config)


def test_tables_columns():
    through_meta = Student.ormar_config.model_fields["courses"].through.ormar_config
    assert "course_id" in through_meta.table.c
    assert "student_id" in through_meta.table.c
    assert "course_id" in through_meta.model_fields
    assert "student_id" in through_meta.model_fields


@pytest.mark.asyncio
async def test_working_with_changed_through_names():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            to_save = {
                "course_name": "basic1",
                "students": [{"name": "Jack"}, {"name": "Abi"}],
            }
            await Course(**to_save).save_related(follow=True, save_all=True)
            course_check = await Course.objects.select_related("students").get()

            assert course_check.course_name == "basic1"
            assert course_check.students[0].name == "Jack"
            assert course_check.students[1].name == "Abi"

            students = await course_check.students.all()
            assert len(students) == 2

            student = await course_check.students.get(name="Jack")
            assert student.name == "Jack"

            students = await Student.objects.select_related("courses").all(
                courses__course_name="basic1"
            )
            assert len(students) == 2

            course_check = (
                await Course.objects.select_related("students")
                .order_by("students__name")
                .get()
            )
            assert course_check.students[0].name == "Abi"
            assert course_check.students[1].name == "Jack"
