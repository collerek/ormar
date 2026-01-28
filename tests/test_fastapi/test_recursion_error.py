import uuid
from datetime import datetime
from typing import List, Optional

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Json

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
router = FastAPI(lifespan=lifespan(base_ormar_config))
headers = {"content-type": "application/json"}


class User(ormar.Model):
    """
    The user model
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    email: str = ormar.String(unique=True, max_length=100)
    username: str = ormar.String(unique=True, max_length=100)
    password: str = ormar.String(unique=True, max_length=100)
    verified: bool = ormar.Boolean(default=False)
    verify_key: Optional[str] = ormar.String(unique=True, max_length=100, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())

    ormar_config = base_ormar_config.copy(tablename="users")


class UserSession(ormar.Model):
    """
    The user session model
    """

    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)
    user: User = ormar.ForeignKey(User)
    session_key: str = ormar.String(unique=True, max_length=64)
    created_at: datetime = ormar.DateTime(default=datetime.now())

    ormar_config = base_ormar_config.copy(tablename="user_sessions")


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
    description: Optional[str] = ormar.String(max_length=300, nullable=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())
    updated_at: datetime = ormar.DateTime(default=datetime.now())
    user_id: uuid.UUID = ormar.UUID(foreign_key=User.id)
    questions: Json = ormar.JSON(nullable=False)

    ormar_config = base_ormar_config.copy(tablename="quiz")


create_test_database = init_tests(base_ormar_config)


async def get_current_user():
    return await User(email="mail@example.com", username="aa", password="pass").save()


@router.post("/create", response_model=Quiz)
async def create_quiz_lol(
    quiz_input: QuizInput, user: User = Depends(get_current_user)
):
    quiz = Quiz(**quiz_input.model_dump(), user_id=user.id)
    return await quiz.save()


@pytest.mark.asyncio
async def test_quiz_creation():
    transport = ASGITransport(app=router)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(router):
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
        response = await client.post("/create", json=payload)
        assert response.status_code == 200
