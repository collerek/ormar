# type: ignore
import uuid
from typing import List

import databases
import pytest
import sqlalchemy

import ormar
from ormar.exceptions import ModelError, QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    email: str = ormar.String(nullable=False, max_length=100)


class Project(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "owner_id")]

    id: int = ormar.Integer()
    owner: User = ormar.ForeignKey(User, name="owner_id")
    name: str = ormar.String(nullable=False, max_length=100)


class Tag(ormar.Model):
    class Meta(BaseMeta):
        constraints = [ormar.PrimaryKeyConstraint("id", "owner_id", "project_id")]

    id: int = ormar.Integer()
    owner: User = ormar.ForeignKey(User, name="owner_id")
    tag_project: Project = ormar.ForeignKey(
        Project, names={"owner_id": "owner_id", "id": "project_id"}
    )
    name: str = ormar.String(nullable=False, max_length=100)


class TaskTag(ormar.Model):
    class Meta(BaseMeta):
        tablename = "task_tags"

    id: int = ormar.Integer(primary_key=True)


class Task(ormar.Model):
    class Meta(BaseMeta):
        tablename = "tasks"
        constraints = [ormar.PrimaryKeyConstraint("id", "owner", "project_id")]

    id: int = ormar.Integer()
    owner: User = ormar.ForeignKey(User)
    project: Project = ormar.ForeignKey(
        Project, names={"owner_id": "owner", "id": "project_id"}
    )
    description: str = ormar.String(nullable=False, max_length=200)
    completed: bool = ormar.Boolean(nullable=False, default=False)
    tags: List[Tag] = ormar.ManyToMany(Tag, through=TaskTag)


class SimpleComposite(ormar.Model):
    class Meta(BaseMeta):
        tablename = "simple_composites"
        constraints = [ormar.PrimaryKeyConstraint("id", "sort_order")]

    id: int = ormar.Integer()
    sort_order: int = ormar.Integer()
    name: int = ormar.String(max_length=100)


class SimpleCompositeAlias(ormar.Model):
    class Meta(BaseMeta):
        tablename = "simple_composites_alias"
        constraints = [ormar.PrimaryKeyConstraint("id", "order_no")]

    id: int = ormar.Integer()
    sort_order: int = ormar.Integer(name="order_no")
    name: int = ormar.String(max_length=100)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


################
# Models internals tests
################


def test_models_have_all_expected_fields():
    assert len(Project.Meta.model_fields) == 5
    # own fields
    assert "id" in Project.Meta.model_fields
    assert "name" in Project.Meta.model_fields
    # relations
    assert "owner" in Project.Meta.model_fields
    assert "tags" in Project.Meta.model_fields
    assert "tasks" in Project.Meta.model_fields

    assert len(Tag.Meta.model_fields) == 7
    assert "id" in Tag.Meta.model_fields
    assert "name" in Tag.Meta.model_fields

    # TODO: verify if project_id is needed in model_fields and __fields__
    assert "tag_project" in Tag.Meta.model_fields
    assert "project_id" in Tag.Meta.model_fields

    assert "owner" in Tag.Meta.model_fields
    assert "tasks" in Tag.Meta.model_fields
    assert "tasktag" in Tag.Meta.model_fields

    assert len(Task.Meta.model_fields) == 8
    assert "id" in Task.Meta.model_fields
    assert "description" in Task.Meta.model_fields
    assert "completed" in Task.Meta.model_fields

    # TODO: verify if project_id is needed in model_fields and __fields__
    assert "project" in Task.Meta.model_fields
    assert "project_id" in Task.Meta.model_fields

    assert "owner" in Task.Meta.model_fields
    assert "tags" in Task.Meta.model_fields
    assert "tasktag" in Task.Meta.model_fields

    assert len(TaskTag.Meta.model_fields) == 3
    assert "id" in TaskTag.Meta.model_fields
    assert "tag" in TaskTag.Meta.model_fields
    assert "task" in TaskTag.Meta.model_fields


def test_models_have_expected_db_columns():
    assert len(Project.Meta.table.columns) == 3
    assert "id" in Project.Meta.table.columns
    assert "owner_id" in Project.Meta.table.columns
    assert "name" in Project.Meta.table.columns

    assert len(Tag.Meta.table.columns) == 4
    assert "id" in Tag.Meta.table.columns
    assert "owner_id" in Tag.Meta.table.columns
    assert "project_id" in Tag.Meta.table.columns
    assert "name" in Tag.Meta.table.columns

    assert len(Task.Meta.table.columns) == 5
    assert "id" in Task.Meta.table.columns
    assert "owner" in Task.Meta.table.columns
    assert "project_id" in Task.Meta.table.columns
    assert "description" in Task.Meta.table.columns
    assert "completed" in Task.Meta.table.columns

    assert len(TaskTag.Meta.table.columns) == 7
    assert "id" in TaskTag.Meta.table.columns
    assert "task_owner" in TaskTag.Meta.table.columns
    assert "task_project_id" in TaskTag.Meta.table.columns
    assert "task_id" in TaskTag.Meta.table.columns
    assert "tag_owner_id" in TaskTag.Meta.table.columns
    assert "tag_project_id" in TaskTag.Meta.table.columns
    assert "tag_id" in TaskTag.Meta.table.columns


################
# PK tests
################


@pytest.mark.asyncio
async def test_simple_composite_pk_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            await SimpleComposite(id=1, sort_order=1, name="Test1").save()
            await SimpleComposite(id=1, sort_order=2, name="Test2").save()

            check = await SimpleComposite.objects.order_by(
                SimpleComposite.sort_order.desc()
            ).all()
            assert check[0].name == "Test2"
            assert check[1].name == "Test1"

            assert SimpleComposite.pk_type == (int, int)

            await check[0].delete()
            await check[1].delete()
            with pytest.raises(ormar.NoMatch):
                await SimpleComposite.objects.get()


@pytest.mark.asyncio
async def test_simple_composite_pk_crud_alias():
    async with database:
        async with database.transaction(force_rollback=True):
            simple = await SimpleCompositeAlias(id=1, sort_order=1, name="Test3").save()
            simple2 = await SimpleCompositeAlias(
                id=1, sort_order=2, name="Test4"
            ).save()

            await SimpleCompositeAlias(
                pk={"id": 3, "sort_order": 3}, name="Test5"
            ).save()

            check = await SimpleCompositeAlias.objects.order_by(
                SimpleCompositeAlias.sort_order.desc()
            ).all()
            assert check[0].name == "Test5"
            assert check[1].name == "Test4"
            assert check[2].name == "Test3"

            assert SimpleCompositeAlias.pk_type == (int, int)

            check2 = await SimpleCompositeAlias.objects.get(pk=simple)
            assert check2.name == "Test3"

            check3 = await SimpleCompositeAlias.objects.get(
                id=simple2.id, sort_order=simple2.sort_order
            )
            assert check3.name == "Test4"


@pytest.mark.asyncio
async def test_composite_pk_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            user_beth = User(email="beth@example.com")
            await user_beth.save()
            project_bedroom = await Project.objects.create(
                id=1, owner=user_beth, name="Clean up the bedroom"
            )
            task_underwear = Task(
                id=14,
                owner=user_beth,
                project=project_bedroom,
                description="Collect underwear",
                completed=False,
            )
            await task_underwear.save()

            task = await Task.objects.get(description="Collect underwear")
            assert task.pk == task_underwear.pk
            assert isinstance(task.project, ormar.Model)
            await task.project.load()
            assert task.project.name == "Clean up the bedroom"

            task.project.name = "Make bedroom appear clean"
            await task.project.update()
            project = await Project.objects.get(name="Make bedroom appear clean")
            assert project.pk == project_bedroom.pk
            assert isinstance(project, ormar.Model)


@pytest.mark.asyncio
async def test_composite_fk_crud_from_dict():
    async with database:
        async with database.transaction(force_rollback=True):
            user_beth = User(email="beth@example.com")
            await user_beth.save()
            project_bedroom = await Project.objects.create(
                id=1, owner=user_beth, name="Clean up the bedroom"
            )
            # TODO: Check if this should be owner or owner_id?
            task_underwear = await Task(
                id=14,
                owner=user_beth,
                project=dict(id=project_bedroom.id, owner=user_beth.id),
                description="Collect underwear",
                completed=False,
            ).save()

            task = await Task.objects.select_related(Task.project).get(
                description="Collect underwear"
            )
            assert task.pk == task_underwear.pk
            assert isinstance(task.project, ormar.Model)
            assert task.project == project_bedroom
            assert task.project.name == "Clean up the bedroom"


@pytest.mark.asyncio
async def test_many_to_many_basic_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            user_beth = User(email="beth@example.com")
            await user_beth.save()
            project_bedroom = await Project.objects.create(
                id=1, owner=user_beth, name="Clean up the bedroom"
            )

            tag_urgent = Tag(
                id=12, owner=user_beth, tag_project=project_bedroom, name="URGENT!"
            )
            tag_medium = Tag(
                id=13,
                owner=user_beth,
                tag_project=project_bedroom,
                name="Fine if mum can't smell it",
            )
            await tag_urgent.save()
            await tag_medium.save()

            task_monster = Task(
                id=15,
                owner=user_beth,
                project=project_bedroom,
                description="Feed the monster under the bed",
                completed=False,
            )
            await task_monster.save()
            await task_monster.tags.add(tag_medium)
            await task_monster.tags.add(tag_urgent)

            await task_monster.tags.all()
            assert task_monster.tags is not None and len(task_monster.tags) == 2
            await task_monster.tags.remove(tag_medium)
            all_tags = await task_monster.tags.all()
            assert len(all_tags) == 1


@pytest.mark.asyncio
async def test_reverse_relation_basic_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            user_beth = User(email="beth@example.com")
            await user_beth.save()
            project_bedroom = await Project.objects.create(
                id=1, owner=user_beth, name="Clean up the bedroom"
            )
            task_monster = Task(
                id=15,
                owner=user_beth,
                project=project_bedroom,
                description="Feed the monster under the bed",
                completed=False,
            )
            await task_monster.save()

            await user_beth.tasks.all()
            assert len(user_beth.tasks) == 1
            assert user_beth.tasks[0] == task_monster

            user_check = await User.objects.select_related("tasks").get(
                email="beth@example.com"
            )
            assert len(user_check.tasks) == 1
            assert user_check.tasks[0] == task_monster


@pytest.mark.asyncio
async def test_reverse_relation_compound_crud():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User(email="timmy@example.com").save()
            project_mount_doom = await Project.objects.create(
                id=90, owner=user, name="Destroy the ring"
            )
            task_adventure = await Task(
                id=178,
                owner=user,
                project=project_mount_doom,
                description="Go on an adventure!",
                completed=False,
            ).save()

            project_check = await Project.objects.select_related("tasks").get(
                name="Destroy the ring"
            )
            assert project_check.tasks[0] == task_adventure
            assert len(project_check.tasks)
            assert project_check.owner.pk == user.pk
            assert project_check.owner.email is None


@pytest.mark.asyncio
async def test_error_multiple_pk_declarations():
    with pytest.raises(ormar.ModelDefinitionError):

        class MultiPk(ormar.Model):
            class Meta:
                database = database
                metadata = metadata
                constraints = [
                    ormar.PrimaryKeyConstraint("id_1"),
                ]

            id_1: int = ormar.Integer()
            id_2: int = ormar.Integer(primary_key=True)


@pytest.mark.asyncio
async def test_error_mixed_pk_declarations():
    with pytest.raises(ormar.ModelDefinitionError):

        class MixedPk(ormar.Model):
            class Meta:
                constraints = [
                    ormar.PrimaryKeyConstraint("id_1", "id_2"),
                ]

            id_1: int = ormar.Integer()
            id_2: int = ormar.Integer(primary_key=True)


@pytest.mark.asyncio
async def test_error_when_setting_part_of_pk_none():
    async with database:
        async with database.transaction(force_rollback=True):
            user = User(email="tom@example.com")
            await user.save()
            project = Project(id=2, owner=user, name="Doom impending")
            await project.save()

            project.owner = None
            with pytest.raises(ormar.exceptions.ModelPersistenceError) as exc:
                await project.update()
            # TODO: text exc message


################
# FK tests
################


@pytest.mark.asyncio
async def test_init_fk_column_directly_fails():
    async with database:
        async with database.transaction(force_rollback=True):
            user = User(email="tom@example.com")
            await user.save()

            with pytest.raises(ModelError):
                Project(owner_id=user.id, name="A failed endeavour")

            with pytest.raises(ModelError) as exc:
                Tag(project_id=1, id=10, owner=user, name="TestTag")
            assert str(exc.value) == "You cannot set field project_id directly."


@pytest.mark.asyncio
async def test_set_fk_column_directly_fails():
    async with database:
        async with database.transaction(force_rollback=True):
            user_1 = User(email="tim@example.com")
            user_2 = User(email="tam@example.com")
            await user_1.save()
            await user_2.save()
            project = Project(owner=user_1, name="So far so good", id=4)
            await project.save()

            with pytest.raises(ValueError):
                project.owner_id = user_2.id


@pytest.mark.asyncio
async def test_set_fk_existing_technical_column_directly_fails():
    async with database:
        async with database.transaction(force_rollback=True):
            user_1 = await User(email="tim@example.com").save()
            project = await Project(owner=user_1, name="So far so good", id=4).save()
            tag = await Tag(
                tag_project=project, id=10, owner=user_1, name="TestTag"
            ).save()

            with pytest.raises(ormar.ModelError) as exc:
                tag.project_id = 123
            assert (
                "You cannot set field project_id directly. "
                "Use tag_project relation to set the field"
            ) in str(exc.value)


@pytest.mark.asyncio
async def test_set_compound_pk_wo_dict_fails():
    async with database:
        async with database.transaction(force_rollback=True):
            user_1 = User(email="tim@example.com")
            await user_1.save()
            project = Project(owner=user_1, name="So far so good", id=4)
            await project.save()

            with pytest.raises(ormar.ModelDefinitionError) as exc:
                project.pk = 12
            assert "Compound primary key can be set only with dictionary" in str(
                exc.value
            )


@pytest.mark.asyncio
async def test_get_fk_column_directly_fails():
    async with database:
        async with database.transaction(force_rollback=True):
            user = User(email="tom@example.com")
            await user.save()
            project = Project(id=12, owner=user, name="Doom impending")
            await project.save()
            tag = Tag(tag_project=project, id=10, owner=user, name="TestTag")

            with pytest.raises(AttributeError):
                project.owner_id

            with pytest.raises(ormar.ModelError) as exc:
                tag.project_id
            assert "You cannot access field project_id directly" in str(exc.value)


@pytest.mark.asyncio
async def test_composite_fk_reverse_relation_created():
    async with database:
        async with database.transaction(force_rollback=True):
            user = User(email="tom@example.com")
            await user.save()
            project = Project(id=124, owner=user, name="Find inner peace")
            await project.save()
            task = Task(
                id=125,
                owner=user,
                project=project,
                description="Meditate 25 hours a day",
                completed=True,
            )
            await task.save()
            assert len(project.tasks) == 1
            assert isinstance(project.tasks[0], ormar.Model)
            assert project.tasks[0].pk == task.pk


################
# Consistency with pydantic
################


@pytest.mark.asyncio
async def test_correct_pydantic_dict_with_composite_keys():
    async with database:
        async with database.transaction(force_rollback=True):
            user = User(email="juan@example.com")
            await user.save()
            project = Project(id=15, owner=user, name="Get rich fast")
            await project.save()
            task = Task(
                id=23,
                owner=user,
                project=project,
                description="Buy lots of Bitcoin",
                completed=False,
            )
            await task.save()

            loaded_user = await User.objects.get(email="juan@example.com")
            await loaded_user.load_all(follow=True)
            expected_user_dict = {
                "email": user.email,
                "id": user.id,
                "projects": [
                    {
                        "id": 15,
                        "name": "Get rich fast",
                        "owner": user.id,
                        "tags": [],
                        "tasks": [
                            {
                                "completed": False,
                                "description": "Buy lots of Bitcoin",
                                "id": 23,
                                "owner": user.id,
                                "project": {"id": 15, "owner_id": user.id},
                                "project_id": None,
                                "tags": [],
                            }
                        ],
                    }
                ],
                "tags": [],
                "tasks": [
                    {
                        "completed": False,
                        "description": "Buy lots of Bitcoin",
                        "id": 23,
                        "owner": user.id,
                        "project": {"id": 15, "owner": user.id, "tags": []},
                        "project_id": None,
                        "tags": [],
                    }
                ],
            }
            assert loaded_user.dict() == expected_user_dict
            # TODO: Remove project_id (is_denied fields)?
            loaded_project = await Project.objects.get(name="Get rich fast")
            await loaded_project.load_all(follow=True)
            expected_project_dict = {
                "id": 15,
                "name": "Get rich fast",
                "owner": {
                    "email": "juan@example.com",
                    "id": loaded_user.id,
                    "tags": [],
                    "tasks": [
                        {
                            "completed": False,
                            "description": "Buy lots of Bitcoin",
                            "id": 23,
                            "owner": user.id,
                            "project": {"id": 15, "owner_id": user.id},
                            # TODO: Populate project_id if not removed?
                            "project_id": None,
                            "tags": [],
                        }
                    ],
                },
                "tags": [],
                "tasks": [
                    {
                        "completed": False,
                        "description": "Buy lots of Bitcoin",
                        "id": 23,
                        "owner": {
                            "email": "juan@example.com",
                            "id": loaded_user.id,
                            "tags": [],
                        },
                        "project": {"id": 15, "owner_id": user.id},
                        "project_id": None,
                        "tags": [],
                    }
                ],
            }
            assert loaded_project.dict() == expected_project_dict


@pytest.mark.asyncio
async def test_manual_complex_prefix_for_duplicated_relations():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User(email="juanita@example.com").save()
            project = await Project(id=15, owner=user, name="Get rich fast").save()
            task = Task(
                id=23,
                owner=user,
                project=project,
                description="Buy lots of Bitcoin",
                completed=False,
            )
            await task.save()
            tag_urgent = await Tag(
                id=12, owner=user, tag_project=project, name="URGENT!"
            ).save()
            await task.tags.add(tag_urgent)

            loaded_user = (
                await User.objects.select_related(
                    [User.projects.tasks.tags, User.tasks.project.tasks.tags]
                )
                .filter(User.tasks.project.tasks.tags.name == "URGENT!")
                .get(email="juanita@example.com")
            )
            assert loaded_user.projects[0].name == "Get rich fast"
            assert (
                loaded_user.tasks[0].project.tasks[0].description
                == "Buy lots of Bitcoin"
            )
            assert loaded_user.tasks[0].project.tasks[0].tags[0].name == "URGENT!"

            assert loaded_user.dict() == {
                "email": "juanita@example.com",
                "id": user.id,
                "projects": [
                    {
                        "id": 15,
                        "name": "Get rich fast",
                        "owner": user.id,
                        "tags": [],
                        "tasks": [
                            {
                                "completed": False,
                                "description": "Buy lots of Bitcoin",
                                "id": 23,
                                "owner": user.id,
                                "project": {"id": 15, "owner_id": user.id},
                                "project_id": None,
                                "tags": [
                                    {
                                        "id": 12,
                                        "name": "URGENT!",
                                        "project_id": None,
                                        "tasktag": {"id": 1, "tag": None, "task": None},
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "tags": [],
                "tasks": [
                    {
                        "completed": False,
                        "description": "Buy lots of Bitcoin",
                        "id": 23,
                        "owner": user.id,
                        "project": {
                            "id": 15,
                            "name": "Get rich fast",
                            "owner": user.id,
                            "tags": [],
                        },
                        "project_id": None,
                        "tags": [],
                    }
                ],
            }


################
# pk property working correctly
################


@pytest.mark.asyncio
async def test_scalar_pk_property():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User.objects.create(email="torben@example.com")
            assert isinstance(user.pk, uuid.UUID)
            assert user.pk == user.id


@pytest.mark.asyncio
async def test_filter_by_pk_with_instance():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User.objects.create(email="ai@example.com")
            project = await Project.objects.create(owner=user, name="Gardening", id=5)

            check = await Project.objects.get(pk=project)
            assert check.pk == project.pk

            check2 = await Project.objects.get(pk=project.pk)
            assert check2.pk == project.pk

            with pytest.raises(QueryDefinitionError) as exc:
                await Project.objects.filter(pk__lte=project).get()
            assert (
                "You cannot use ormar.Model in filters different than equals!"
                in str(exc.value)
            )


@pytest.mark.asyncio
async def test_get_composite_pk_property():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User.objects.create(email="ai@example.com")

            project = await Project.objects.create(owner=user, name="Gardening", id=5)
            assert isinstance(project.pk, dict)
            assert len(project.pk) == 2
            assert set(project.pk.keys()) == {"id", "owner_id"}
            assert project.pk["owner_id"] == user.pk

            task = await Task.objects.create(
                id=234,
                owner=user,
                project=project,
                description="Down with the weeds!",
                completed=False,
            )
            assert isinstance(task.pk, dict)
            assert len(task.pk) == 3
            assert set(task.pk.keys()) == {"id", "owner", "project_id"}
            assert task.pk["owner"] == user.pk
            assert task.pk["project_id"] == project.pk.get("id")


@pytest.mark.asyncio
async def test_set_composite_pk_property():
    async with database:
        async with database.transaction(force_rollback=True):
            user_tian = await User(email="tian@example.com").save()
            user_josie = await User(email="josie@example.com").save()

            project = await Project(
                id=345, owner=user_tian, name="Become an influencer",
            ).save()
            project.pk = {"id": 445, "owner": user_josie}
            assert project.id == 445
            assert project.owner == user_josie
            await project.save()

            project = await Project.objects.get(id=445, owner=user_josie.pk)
            assert project.id == 445
            assert project.owner.pk == user_josie.pk
            project.name = "Become an entrepreneur"
            await project.update()

            await Project(
                pk=dict(id=346, owner=user_tian), name="Become an insta model",
            ).save()
            project2 = await Project.objects.get(id=346, owner=user_tian.pk)
            assert project2.name == "Become an insta model"

            await Project(pk=project2.pk, name="Become an CoD soldier",).update()
            project3 = await Project.objects.get(id=346, owner=user_tian.pk)
            assert project3.name == "Become an CoD soldier"

            tag1 = await Tag(
                pk=dict(project_id=project.id, id=1112, owner_id=user_tian.id),
                name="TestTag",
            ).save()
            tag2 = Tag(pk=tag1.pk, name="TestTag2")
            assert tag1.pk == tag2.pk
            await tag2.update()
            check = await Tag.objects.get(pk=tag2.pk)
            assert check.name == "TestTag2"


@pytest.mark.asyncio
async def test_bulk_create_and_update():
    async with database:
        async with database.transaction(force_rollback=True):
            user = await User(email="tom@example.com").save()
            project = await Project(id=12, owner=user, name="Doom impending").save()
            tags = [
                Tag(tag_project=project, id=k + 1, owner=user, name=f"TestTag{k + 1}")
                for k in range(5)
            ]
            await Tag.objects.bulk_create(tags)

            check = await Tag.objects.all()
            assert len(check) == 5
            assert [f"TestTag{k + 1}" for k in range(5)] == [
                inst.name for inst in check
            ]

            for tag in check:
                tag.name = "NewTag"

            await Tag.objects.bulk_update(check)

            check2 = await Tag.objects.select_related(Tag.tag_project).all()
            assert len(check2) == 5
            assert all(x.name == "NewTag" for x in check2)


# TODO:
# Register Foreign Key to field with multi column pk
# (V)   -> Reuse the same ForeignKey function, instead of name pass names dict
# (V)   -> In names dict in fk always use real columns names (aliases) not ormar names
# (V)   -> During registration check if model already have all fields mentioned in names
# (V) -> If not all fields are already present
# (V)       -> create missing fields based on to pk type of target model
#   -> Names are optional and if not provided all fields are created
# (V) Resolve complex fks before complex pks as fks might create needed fields
# Allow for nested fields in relation?
# New method to resolve fields instead of direct model_fields access?
# Add to relation
# remove from relation
# select related
#   -> normal,
#   -> reverse,
#   -> many to many
# prefetch related
#   -> normal,
#   -> reverse,
#   -> many to many
# fix dict()
# fix __repr__ for denied fields
