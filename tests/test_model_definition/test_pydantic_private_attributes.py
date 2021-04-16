from typing import List

import databases
import sqlalchemy
from pydantic import PrivateAttr

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Subscription(ormar.Model):
    class Meta(BaseMeta):
        tablename = "subscriptions"

    id: int = ormar.Integer(primary_key=True)
    stripe_subscription_id: str = ormar.String(nullable=False, max_length=256)

    _add_payments: List[str] = PrivateAttr(default_factory=list)

    def add_payment(self, payment: str):
        self._add_payments.append(payment)


def test_private_attribute():
    sub = Subscription(stripe_subscription_id="2312312sad231")
    sub.add_payment("test")
