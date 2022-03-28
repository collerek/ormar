import json
from datetime import datetime
import uuid
from typing import List

import databases
import pytest
import sqlalchemy
from fastapi import Depends, FastAPI
from pydantic import BaseModel, Json
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

router = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)
router.state.database = database

headers = {"content-type": "application/json"}


@router.on_event("startup")
async def startup() -> None:
    database_ = router.state.database
    if not database_.is_connected:
        await database_.connect()


@router.on_event("shutdown")
async def shutdown() -> None:
    database_ = router.state.database
    if database_.is_connected:
        await database_.disconnect()


class User(ormar.Model):
    """
    The user model
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    email: str = ormar.String(unique=True, max_length=100)
    username: str = ormar.String(unique=True, max_length=100)
    password: str = ormar.String(unique=True, max_length=100)
    verified: bool = ormar.Boolean(default=False)
    verify_key: str = ormar.String(unique=True, max_length=100, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())

    class Meta:
        tablename = "users"
        metadata = metadata
        database = database


class UserSession(ormar.Model):
    """
    The user session model
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    user: User = ormar.ForeignKey(User)
    session_key: str = ormar.String(unique=True, max_length=64)
    created_at: datetime = ormar.DateTime(default=datetime.now())

    class Meta:
        tablename = "user_sessions"
        metadata = metadata
        database = database


class QuizAnswer(BaseModel):
    right: bool
    answer: str


class QuizQuestion(BaseModel):
    question: str
    answers: List[QuizAnswer]


class QuizInput(BaseModel):
    title: str
    description: str
    questions: List[QuizQuestion]


class Quiz(ormar.Model):
    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    title: str = ormar.String(max_length=100)
    description: str = ormar.String(max_length=300, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())
    updated_at: datetime = ormar.DateTime(default=datetime.now())
    user_id: uuid.UUID = ormar.UUID(foreign_key=User.id)
    questions: Json = ormar.JSON(nullable=False)

    class Meta:
        tablename = "quiz"
        metadata = metadata
        database = database


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


async def get_current_user():
    return await User.objects.get()


@router.post("/create", response_model=Quiz)
async def create_quiz_lol(
    quiz_input: QuizInput, user: User = Depends(get_current_user)
):
    quiz = Quiz(**quiz_input.dict(), user_id=user.id)
    return await quiz.save()


@pytest.mark.asyncio()
async def test_quiz_creation():
    async with database:
        await User(email="mail@example.com", username="aa", password="pass").save()
        client = TestClient(app=router)
        payload = {
            "title": "Some test question",
            "description": "A description",
            "questions": [
                {
                    "question": "Is ClassQuiz cool?",
                    "answers": [
                        {"right": True, "answer": "Yes"},
                        {"right": False, "answer": "No"},
                    ],
                },
                {
                    "question": "Do you like open source?",
                    "answers": [
                        {"right": True, "answer": "Yes"},
                        {"right": False, "answer": "No"},
                        {"right": False, "answer": "Maybe"},
                    ],
                },
            ],
        }
        response = client.post("/create", data=json.dumps(payload))
        assert response.status_code == 200
