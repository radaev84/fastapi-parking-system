from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.main.app import create_app
from app.main.app import db as _db
from app.main.models import Client, ClientParking, Parking


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "parking: mark test to run only parking tests")


@pytest.fixture
def app() -> Any:
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://:memory:"

    with _app.app_context():
        _db.create_all()

        client_with_card_1 = Client(
            id=1,
            name="Test_1",
            surname="User_1",
            credit_card="1234-ABCD-9012-3456",
            car_number="A456BC",
        )
        client_no_card = Client(
            id=2,
            name="Test_2",
            surname="User_2",
            car_number="A098BC",
        )
        client_with_card_2 = Client(
            id=3,
            name="Test_3",
            surname="User_3",
            credit_card="5434-AB3D-1231-0456",
            car_number="A111MC",
        )
        parked_client_with_card = Client(
            id=4,
            name="Test_4",
            surname="User_4",
            credit_card="5431-AB3D-1231-0456",
            car_number="A121MC",
        )
        parked_client_no_card = Client(
            id=5,
            name="Test_5",
            surname="User_5",
            car_number="A021MC",
        )

        parking_ready = Parking(
            id=1,
            address="ул. Гороховая, 1",
            count_places=5,
            count_available_places=3,
            opened=True,
        )
        parking_closed = Parking(
            id=2,
            address="ул. Старая, 2",
            count_places=2,
            count_available_places=1,
            opened=False,
        )
        parking_full = Parking(
            id=3,
            address="ул. Новая, 3",
            count_places=2,
            count_available_places=0,
            opened=True,
        )
        parking_with_clients = Parking(
            id=4,
            address="ул. Новая, 56",
            count_places=5,
            count_available_places=3,
            opened=True,
        )

        parked_client_with_card_parking = ClientParking(
            id=1,
            client_id=4,
            parking_id=4,
            time_in=datetime.now(timezone.utc) - timedelta(days=1),
        )
        parked_client_no_card_parking = ClientParking(
            id=2,
            client_id=5,
            parking_id=4,
            time_in=datetime.now(timezone.utc) - timedelta(days=2),
        )

        _db.session.add(client_with_card_1)
        _db.session.add(client_no_card)
        _db.session.add(client_with_card_2)
        _db.session.add(parked_client_with_card)
        _db.session.add(parked_client_no_card)

        _db.session.add(parking_ready)
        _db.session.add(parking_closed)
        _db.session.add(parking_full)
        _db.session.add(parking_with_clients)

        _db.session.add(parked_client_with_card_parking)
        _db.session.add(parked_client_no_card_parking)

        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def factory_app() -> Any:
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://:memory:"

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app: Any) -> Any:
    client = app.test_client()
    yield client


@pytest.fixture
def db(factory_app: Any) -> Any:
    with factory_app.app_context():
        yield _db
