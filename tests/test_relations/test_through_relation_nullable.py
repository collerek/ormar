import pytest
import sqlalchemy

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Subject(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trn_subjects")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Student(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trn_students")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    subjects = ormar.ManyToMany(Subject)


class StudentStrict(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trn_students_strict")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    subjects = ormar.ManyToMany(
        Subject,
        through_relation_nullable=False,
        through_reverse_relation_nullable=False,
    )


class StudentOwnerOnly(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trn_students_owner_only")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    subjects = ormar.ManyToMany(
        Subject,
        through_relation_nullable=False,
    )


class StudentReverseOnly(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="trn_students_reverse_only")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    subjects = ormar.ManyToMany(
        Subject,
        through_reverse_relation_nullable=False,
    )


create_test_database = init_tests(base_ormar_config)


def _through_table(model, field_name):
    return model.ormar_config.model_fields[field_name].through.ormar_config.table


def test_default_through_columns_are_nullable():
    table = _through_table(Student, "subjects")
    assert table.c["student"].nullable is True
    assert table.c["subject"].nullable is True


def test_through_relation_nullable_false_sets_owner_column_not_null():
    table = _through_table(StudentOwnerOnly, "subjects")
    assert table.c["studentowneronly"].nullable is False
    assert table.c["subject"].nullable is True


def test_through_reverse_relation_nullable_false_sets_target_column_not_null():
    table = _through_table(StudentReverseOnly, "subjects")
    assert table.c["studentreverseonly"].nullable is True
    assert table.c["subject"].nullable is False


def test_both_through_columns_can_be_not_null():
    table = _through_table(StudentStrict, "subjects")
    assert table.c["studentstrict"].nullable is False
    assert table.c["subject"].nullable is False


@pytest.mark.asyncio
async def test_m2m_with_non_nullable_through_columns_works_at_runtime():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            subject = await Subject.objects.create(name="math")
            student = await StudentStrict.objects.create(name="Alice")
            await student.subjects.add(subject)

            fetched = await StudentStrict.objects.select_related("subjects").get(
                id=student.id
            )
            assert len(fetched.subjects) == 1
            assert fetched.subjects[0].name == "math"


@pytest.mark.asyncio
async def test_insert_null_into_non_nullable_through_column_fails():
    async with base_ormar_config.database:
        subject = await Subject.objects.create(name="chemistry")
        through_table = _through_table(StudentStrict, "subjects")

        async with base_ormar_config.database.connection() as conn:
            with pytest.raises(sqlalchemy.exc.IntegrityError):
                await conn.execute(
                    through_table.insert().values(
                        studentstrict=None, subject=subject.id
                    )
                )

            with pytest.raises(sqlalchemy.exc.IntegrityError):
                await conn.execute(
                    through_table.insert().values(studentstrict=None, subject=None)
                )
