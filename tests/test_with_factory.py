from typing import Any

from app.main.models import Client, Parking

from .factories import ClientFactory, ParkingFactory


def test_create_client(db: Any) -> None:
    batch = 5
    clients = ClientFactory.create_batch(batch)
    db.session.commit()
    for client in clients:
        assert client.id is not None
    assert len(db.session.query(Client).all()) == batch


def test_create_product(db: Any) -> None:
    batch = 5
    parkings = ParkingFactory.create_batch(batch)
    db.session.commit()
    for parking in parkings:
        assert parking.id is not None
    assert len(db.session.query(Parking).all()) == batch
