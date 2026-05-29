import random

import factory
import factory.fuzzy as fuzzy
from faker import Faker

from app.main.app import db
from app.main.models import Client, Parking

fake = Faker()


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    credit_card = factory.LazyFunction(
        lambda: (
            fake.credit_card_number(card_type="visa") if random.random() > 0.5 else None
        )
    )
    car_number = fuzzy.FuzzyText(length=6)


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = fuzzy.FuzzyText(prefix="ул. ", length=20)
    opened = fuzzy.FuzzyChoice([True, False])
    count_places = factory.Faker("random_int", min=5, max=100)
    count_available_places = factory.LazyAttribute(lambda x: random.randrange(0, 100))
