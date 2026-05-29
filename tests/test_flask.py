import pytest
from app.main.models import Parking, ClientParking


@pytest.mark.parametrize("route", ["/clients", "/clients/1"])
def test_route_status(client, route):
    """Проверка, что все GET-методы возвращают код 200."""

    rv = client.get(route)

    assert rv.status_code == 200


def test_create_client(client):
    """Создание клиента."""

    creation_passed = client.post(
        "/clients",
        json={
            "name": "Test",
            "surname": "User",
            "credit_card": "1234-5678-9012-3456",
            "car_number": "A123BC",
        },
    )
    creation_failed = client.post("/clients", json={"name": "Test", "surname": "User"})

    assert creation_failed.status_code == 400
    assert creation_passed.status_code == 201
    data = creation_passed.get_json()
    assert "id" in data


def test_create_parking(client):
    """Создание парковки."""

    creation_passed = client.post(
        "/parkings",
        json={
            "address": "ул. Ленина, 15",
            "count_places": 50,
            "opened": True,
        },
    )
    creation_failed = client.post("/parkings", json={"address": "ул. Ленина, 25"})

    assert creation_failed.status_code == 400
    assert creation_passed.status_code == 201
    data = creation_passed.get_json()
    assert "id" in data


@pytest.mark.parking
def test_create_client_parking(client):
    """Заезд на парковку."""

    working_parking_id = 1
    working_parking_places_before = Parking.query.get(
        working_parking_id
    ).count_available_places
    created_client_parking = client.post(
        "/client_parkings",
        json={"client_id": 1, "parking_id": working_parking_id},
    )
    working_parking_places_after = Parking.query.get(
        working_parking_id
    ).count_available_places

    parking_closed = client.post(
        "/client_parkings",
        json={"client_id": 3, "parking_id": 2},
    )
    parking_full = client.post(
        "/client_parkings",
        json={"client_id": 3, "parking_id": 3},
    )
    no_client = client.post(
        "/client_parkings",
        json={"client_id": 13, "parking_id": 1},
    )
    no_parking = client.post(
        "/client_parkings",
        json={"client_id": 3, "parking_id": 111},
    )
    missing_field = client.post(
        "/client_parkings",
        json={"another_field_1": 99},
    )

    assert created_client_parking.status_code == 200
    assert "занял место на парковке" in created_client_parking.get_json().get("message")
    assert working_parking_places_after == working_parking_places_before - 1

    assert parking_closed.status_code == 400
    assert "не работает" in parking_closed.get_json().get("error")

    assert parking_full.status_code == 400
    assert "Нет свободных мест" in parking_full.get_json().get("error")

    assert no_client.status_code == 404
    assert "не найден" in no_client.get_json().get("error")

    assert no_parking.status_code == 404
    assert "не найдена" in no_parking.get_json().get("error")

    assert missing_field.status_code == 400
    assert "являются обязательными" in missing_field.get_json().get("error")


@pytest.mark.parking
def test_delete_client_parking(client):
    """Выезд с парковки."""

    working_parking_id = 4
    working_parking_places_before = Parking.query.get(
        working_parking_id
    ).count_available_places
    deleted_client_parking_with_card = client.delete(
        "/client_parkings",
        json={"client_id": 4, "parking_id": working_parking_id},
    )
    working_parking_places_after = Parking.query.get(
        working_parking_id
    ).count_available_places
    working_parking_record = ClientParking.query.get(1)

    deleted_client_parking_no_card = client.delete(
        "/client_parkings",
        json={"client_id": 5, "parking_id": working_parking_id},
    )

    no_client = client.delete(
        "/client_parkings",
        json={"client_id": 13, "parking_id": 1},
    )
    no_parking = client.delete(
        "/client_parkings",
        json={"client_id": 3, "parking_id": 111},
    )
    missing_field = client.delete(
        "/client_parkings",
        json={"another_field_1": 99},
    )

    assert deleted_client_parking_with_card.status_code == 200
    assert "успешно покинул" in deleted_client_parking_with_card.get_json().get(
        "message"
    )
    assert working_parking_places_after == working_parking_places_before + 1
    assert working_parking_record.time_out > working_parking_record.time_in

    assert deleted_client_parking_no_card.status_code == 400
    assert "нет карты для оплаты" in deleted_client_parking_no_card.get_json().get(
        "error"
    )

    assert no_client.status_code == 404
    assert "не найден" in no_client.get_json().get("error")

    assert no_parking.status_code == 404
    assert "не найдена" in no_parking.get_json().get("error")

    assert missing_field.status_code == 400
    assert "являются обязательными" in missing_field.get_json().get("error")
