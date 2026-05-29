from datetime import datetime, timezone
from typing import Any, List, Tuple

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app() -> Any:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///prod.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    from .models import Client, ClientParking, Parking

    with app.app_context():
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception: Any = None) -> None:
        db.session.remove()

    @app.route("/clients", methods=["GET"])
    def get_clients_handler() -> Tuple:
        """Получение списка всех клиентов."""
        clients: List[Client] = db.session.query(Client).all()
        clients_list = [c.to_json() for c in clients]
        return jsonify(clients_list), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client_handler(client_id: int) -> Tuple:
        """Получение информации о клиенте по ID."""
        client: Client = Client.query.get_or_404(client_id)

        return client.to_json(), 200

    @app.route("/clients", methods=["POST"])
    def create_client_handler() -> Tuple:
        """Создание нового клиента"""
        data = request.get_json()
        name = data.get("name")
        surname = data.get("surname")
        credit_card = data.get("credit_card")
        car_number = data.get("car_number")
        if not name or not surname or not credit_card or not car_number:
            return (
                jsonify(
                    {
                        "error": "Поля name, surname, credit_card, car_number являются обязательными"
                    }
                ),
                400,
            )
        new_client = Client(
            name=name, surname=surname, credit_card=credit_card, car_number=car_number
        )
        db.session.add(new_client)
        db.session.commit()
        db.session.refresh(new_client)
        result = new_client.to_json()

        return result, 201

    @app.route("/parkings", methods=["POST"])
    def create_parking_handler() -> Tuple:
        """Создание новой парковочной зоны."""
        data = request.get_json()
        address = data.get("address")
        opened = data.get("opened", True)
        count_places = data.get("count_places")
        count_available_places = data.get("count_places")
        if not address or not opened or not count_places or not count_available_places:
            return (
                jsonify(
                    {
                        "error": "Поля address, opened, count_places, count_available_places являются обязательными"
                    }
                ),
                400,
            )
        new_parking = Parking(
            address=address,
            opened=opened,
            count_places=count_places,
            count_available_places=count_available_places,
        )
        db.session.add(new_parking)
        db.session.commit()
        db.session.refresh(new_parking)
        result = new_parking.to_json()

        return result, 201

    @app.route("/client_parkings", methods=["POST"])
    def enter_parking_handler() -> Tuple:
        """
        Обработка заезда на парковку.
        Проверки: открыта ли парковка, количество свободных мест на парковке уменьшается, фиксируется дата заезда.
        В теле запроса передаются client_id, parking_id.
        """
        data = request.get_json()
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")
        if not client_id or not parking_id:
            return (
                jsonify({"error": "Поля client_id, parking_id являются обязательными"}),
                400,
            )
        client = Client.query.get(client_id)
        parking = Parking.query.get(parking_id)

        if not client:
            return jsonify({"error": "Клиент не найден"}), 404
        if not parking:
            return jsonify({"error": "Парковка не найдена"}), 404
        if not parking.opened:
            return jsonify({"error": "Парковка не работает"}), 400
        if parking.count_available_places <= 0:
            return jsonify({"error": "Нет свободных мест"}), 400

        existing_record = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()
        if existing_record:
            return jsonify({"error": f"Клиент {client} уже на парковке"}), 400

        new_record = ClientParking(
            client_id=client_id,
            parking_id=parking_id,
            time_in=datetime.now(timezone.utc),
        )

        parking.count_available_places -= 1

        db.session.add(new_record)
        db.session.commit()

        return (
            jsonify({"message": f"Клиент {client} занял место на парковке {parking}"}),
            200,
        )

    @app.route("/client_parkings", methods=["DELETE"])
    def exit_parking_handler() -> Tuple:
        """
        Обработка выезда с парковки (количество свободных мест увеличивается, проставляем время выезда).
        В теле запроса передаются client_id, parking_id.
        """
        data = request.get_json()
        client_id = data.get("client_id")
        parking_id = data.get("parking_id")

        if not client_id or not parking_id:
            return (
                jsonify({"error": "Поля client_id, parking_id являются обязательными"}),
                400,
            )

        client = Client.query.get(client_id)
        parking = Parking.query.get(parking_id)

        if not client:
            return jsonify({"error": "Клиент не найден"}), 404
        if not parking:
            return jsonify({"error": "Парковка не найдена"}), 404
        if not client.credit_card:
            return jsonify({"error": "У клиента нет карты для оплаты"}), 400

        record = ClientParking.query.filter_by(
            client_id=client_id, parking_id=parking_id, time_out=None
        ).first()

        if not record:
            return jsonify({"error": "Нет записи о пребывании на парковке"}), 400

        record.time_out = datetime.now(timezone.utc)
        parking.count_available_places += 1
        db.session.commit()

        return (
            jsonify({"message": f"Клиент {client} успешно покинул парковку {parking}"}),
            200,
        )

    return app
