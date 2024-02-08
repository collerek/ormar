from typing import List, Optional

import ormar
import pytest

from tests.settings import create_config
from tests.lifespan import init_tests


base_ormar_config = create_config()


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="test_users")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)


class Signup(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="test_signup")

    id: int = ormar.Integer(primary_key=True)


class Session(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="test_sessions")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255, index=True)
    some_text: str = ormar.Text()
    some_other_text: Optional[str] = ormar.Text(nullable=True)
    teacher: Optional[User] = ormar.ForeignKey(
        User, nullable=True, related_name="teaching"
    )
    students: Optional[List[User]] = ormar.ManyToMany(
        User, through=Signup, related_name="attending"
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_add_students():
    async with base_ormar_config.database:
        for user_id in [1, 2, 3, 4, 5]:
            await User.objects.create(name=f"User {user_id}")

        for name, some_text, some_other_text in [
            ("Session 1", "Some text 1", "Some other text 1"),
            ("Session 2", "Some text 2", "Some other text 2"),
            ("Session 3", "Some text 3", "Some other text 3"),
            ("Session 4", "Some text 4", "Some other text 4"),
            ("Session 5", "Some text 5", "Some other text 5"),
        ]:
            await Session(
                name=name, some_text=some_text, some_other_text=some_other_text
            ).save()

        s1 = await Session.objects.get(pk=1)
        s2 = await Session.objects.get(pk=2)

        users = {}
        for i in range(1, 6):
            user = await User.objects.get(pk=i)
            users[f"user_{i}"] = user
            if i % 2 == 0:
                await s1.students.add(user)
            else:
                await s2.students.add(user)

        assert len(s1.students) > 0
        assert len(s2.students) > 0

        user = await User.objects.select_related("attending").get(pk=1)

        assert user.attending is not None
        assert len(user.attending) > 0

        query = Session.objects.prefetch_related(["students", "teacher"])
        sessions = await query.all()
        assert len(sessions) == 5
