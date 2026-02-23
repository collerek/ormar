import ormar
from pydantic import PrivateAttr

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Subscription(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="subscriptions")

    id: int = ormar.Integer(primary_key=True)
    stripe_subscription_id: str = ormar.String(nullable=False, max_length=256)

    _add_payments: list[str] = PrivateAttr(default_factory=list)

    def add_payment(self, payment: str):
        self._add_payments.append(payment)


create_test_database = init_tests(base_ormar_config)


def test_private_attribute():
    sub = Subscription(stripe_subscription_id="2312312sad231")
    sub.add_payment("test")
