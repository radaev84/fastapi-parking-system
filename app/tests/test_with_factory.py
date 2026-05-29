from .factories import ClientFactory, ParkingFactory
from ..main.models import Client, Parking


def test_create_client(db):
    batch = 5
    clients = ClientFactory.create_batch(batch)
    db.session.commit()
    for client in clients:
        assert client.id is not None
    assert len(db.session.query(Client).all()) == batch


def test_create_product(db):
    batch = 5
    parkings = ParkingFactory.create_batch(batch)
    db.session.commit()
    for parking in parkings:
        assert parking.id is not None
    assert len(db.session.query(Parking).all()) == batch
