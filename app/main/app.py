from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from typing import List
from datetime import datetime, timezone

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///prod.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    from .models import Client, Parking, ClientParking

    with app.app_context():
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route("/clients", methods=["GET"])
    def get_clients_handler():
        """Получение списка всех клиентов."""
        clients: List[Client] = db.session.query(Client).all()
        clients_list = [c.to_json() for c in clients]
        return jsonify(clients_list), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client_handler(client_id):
        """Получение информации о клиенте по ID."""
        client: Client = Client.query.get_or_404(client_id)

        return client.to_json()

    @app.route("/clients", methods=["POST"])
    def create_client_handler():
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
    def create_parking_handler():
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
    def enter_parking_handler():
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
    def exit_parking_handler():
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

    # @app.route("/test_route")
    # def math_route():
    #     """Тестовый роут для расчета степени"""
    #     number = int(request.args.get("number", 0))
    #     result = number ** 2
    #     return jsonify(result)

    # @app.route("/users", methods=['POST'])
    # def create_user_handler():
    #     """Создание нового пользователя"""
    #     name = request.form.get('name', type=str)
    #     email = request.form.get('email', type=str)
    #     surname = request.form.get('surname', type=str)

    #     new_user = User(name=name,
    #                     surname=surname,
    #                     email=email)

    #     db.session.add(new_user)
    #     db.session.commit()

    #     return '', 201

    # @app.route("/users", methods=['GET'])
    # def get_users_handler():
    #     """Получение пользователей"""
    #     users: List[User] = db.session.query(User).all()
    #     users_list = [u.to_json() for u in users]
    #     return jsonify(users_list), 200

    # @app.route("/users/<int:user_id>", methods=['GET'])
    # def get_user_handler(user_id: int):
    #     """Получение пользователя по ид"""
    #     user: User = db.session.query(User).get(user_id)
    #     return jsonify(user.to_json()), 200

    # @app.route("/products", methods=['POST'])
    # def create_product_handler():
    #     """Создание нового продукта пользователя"""
    #     title = request.form.get('title', type=str)
    #     price = request.form.get('price', type=float)
    #     user_id = request.form.get('user_id', type=int)

    #     new_product = Product(title=title,
    #                           price=price,
    #                           user_id=user_id)

    #     db.session.add(new_product)
    #     db.session.commit()
    #     return '', 201

    # @app.route("/products/<int:product_id>", methods=['PATCH'])
    # def update_product_handler(product_id: int):
    #     """
    #     Изменение продукта
    #     """
    #     title = request.form.get('title', type=str)
    #     price = request.form.get('price', type=float)
    #     user_id = request.form.get('user_id', type=int)

    #     product = db.session.query(Product).get(product_id)
    #     if title:
    #         product.title = title
    #     if price:
    #         product.price = price
    #     if user_id:
    #         product.user_id = user_id

    #     db.session.commit()
    #     return '', 201

    # @app.route("/", methods=['GET'])
    # def get_template_handler() -> str:
    #     """Получение UI-интерфейса с продуктами от пользователей"""

    #     products = db.session.query(Product).all()
    #     products_by_users = []
    #     for p in products:
    #         product_obj = dict(**p.to_json(),
    #                            user=p.user.to_json())
    #         products_by_users.append(product_obj)
    #     return render_template("user_products.html",
    #                            products=products_by_users)

    return app
