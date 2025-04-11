"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorites
import re
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


def validar_password(password):
    if len(password) < 3:
        return jsonify({"False": "La contraseña debe tener al menos 4 caracteres"})

    if not password[0].isupper():
        return jsonify({"False": "La contraseña debe comenzar con una letra mayúscula"})

    if not re.search(r'[@!#%+]', password):
        return jsonify({"False": "La contraseña debe contener al menos un símbolo especial (@, !, #, %, +)"})

    return True, ""


def validar_email(email):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(patron, email):
        return True
    return False


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()

    if not users:
        return jsonify({"message": "No existen usuarios"})

    user_serialize = [user.serialize() for user in users if user.is_active]
    return jsonify(user_serialize), 200


@app.route('/users', methods=['POST'])
def add_new_user():
    data = request.json

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "El email ya está registrado"}), 409

    if not name:
        return jsonify({"message": "El usuario debe tener un nombre"}), 400
    if not email:
        return jsonify({"message": "El usuario debe tener un email"}),
    if not validar_email(email):
        return jsonify({"message": "El email no tiene un formato válido"}), 400
    if not password:
        return jsonify({"message": "El usuario debe tener una contraseña"}), 400


    user = User(
        name=name,
        email=email,
        password=password
    )
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Usuario creado con éxito"}), 201
    except Exception as e:
        return jsonify({"message": "Error al crear el usuario", "error": str(e)}), 500


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    exist = User.query.get(user_id)

    if not exist:
        return jsonify({"message": "El usuario no existe"}), 404

    try:
        db.session.delete(exist)
        db.session.commit()
        return jsonify({"message": "El usuario a sido eliminado con exito"}), 200
    except Exception as e:
        return jsonify({"message": "Error al eliminar el usuario", "error": str(e)}), 500


# Enpoints de Characters


@app.route('/people')
def get_all_people():
    characters = Character.query.all()

    if not characters:
        return jsonify({"message": "No se encuentran characters"}), 404

    char_serialize = [char.serialize() for char in characters]
    return jsonify(char_serialize), 200


@app.route('/people/<int:people_id>')
def get_people(people_id):
    character = Character.query.get(people_id)

    if not character:
        return jsonify({"message": "Not found"}), 404

    return jsonify(character.serialize()), 200


@app.route('/people', methods=["POST"])
def add_new_character():
    data = request.json
    name = data.get("name", "").strip()
    specie = data.get("specie", "").strip()

    if not name:
        return jsonify({"message": "El personaje debe tener un nombre"}), 400
    if not specie:
        return jsonify({"message": "El personaje debe ser de una especie"}), 400
    try:
        new_character = Character(name=name, specie=specie)
        db.session.add(new_character)
        db.session.commit()
        return jsonify({
            "message": "Character agregado con éxito",
            "new_character": new_character.serialize()
        }), 201
    except Exception as e:
        return jsonify({"message": "Error al crear el character", "error": str(e)}), 500


@app.route('/people/<int:people_id>', methods=['PUT'])
def edit_people(people_id):
    data = request.json
    name = data.get("name", "").strip()
    specie = data.get("specie", "").strip()

    character = Character.query.get(people_id)

    if not character:
        return jsonify({"message": "Character no encontrado"}), 404

    if not name:
        return jsonify({"message": "El personaje debe tener un nombre"}), 400
    if not specie:
        return jsonify({"message": "El personaje debe tener una especie"}), 400

    character.name = name
    character.specie = specie

    try:
        db.session.commit()
        return jsonify({
            "message": "Personaje actualizado correctamente",
            "character": character.serialize()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al actualizar", "error": str(e)}), 500


@app.route('/people/<int:id>', methods=["DELETE"])
def delete_people(id):
    exist = Character.query.get(id)

    if not exist:
        return jsonify({"message": "Este Character no existe"}), 404

    db.session.delete(exist)
    db.session.commit()
    return jsonify({
        "message": "Character eliminado con exito",
        "character": exist.serialize()
    })


@app.route('/favorite/people/<int:id>', methods=["POST"])
def add_favorit_people(id):
    try:
        character = Character.query.get(id)
        if not character:
            return jsonify({"message": "Character no encontrado"}), 404
        
        exist = Favorites.query.filter_by(id_character=id, id_user=1).first()
        if exist:
            return jsonify({"message": "Already exist"}), 409

        favorite = Favorites(
            id_character=id,
            id_user=1,
            id_planet=None,
            name=character.name,  # Asignar el nombre del Character
            tipo="character"      # Asignar el tipo como "character"
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify(favorite.serialize()), 201
    except Exception as e:
        return jsonify({"message": "Error al agregar el favorito", "error": str(e)}), 500


@app.route('/favorite/people/<int:id>', methods=["DELETE"])
def delete_favorite_people(id):
    favorite = Favorites.query.filter_by(id_character=id, id_user=1).first()

    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite deleted successfully"}), 200


# Enpoints de Planetas


@app.route('/planets')
def get_all_planets():
    planets = Planet.query.all()

    if not planets:
        return jsonify({"message": "No se encontraron planetas"}), 404

    planet_serialize = [planet.serialize() for planet in planets]
    return jsonify(planet_serialize), 200


@app.route('/planets/<int:planet_id>')
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "Not found"}), 404

    return jsonify(planet.serialize()), 200


@app.route('/planets', methods=["POST"])
def add_new_planet():
    data = request.json
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"message": "El planeta debe tener un nombre"}), 400

    try:
        new_planet = Planet(name=name)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify({
            "message": "Planeta agregado con éxito",
            "new_planet": new_planet.serialize()
        }), 201
    except Exception as e:
        return jsonify({"message": "Error al crear el planeta", "error": str(e)}), 500


@app.route('/planets/<int:planet_id>', methods=["PUT"])
def edit_planet(planet_id):
    data = request.get_json()

    if not data:
        return jsonify({"message", "Not found"}), 404

    name = data.get("name", "").strip()

    if not name:
        return jsonify({"message": "El planeta debe tener un name"}), 404

    planet = Planet.query.get(planet_id)

    if not planet:
        return jsonify({"message": "El planeta no existe"}), 404

    planet.name = name

    try:
        db.session.commit()
        return jsonify({
            "message": "Planeta actualizado correctamente",
            "planet": planet.serialize()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al actualizar", "error": str(e)}), 500


@app.route('/planets/<int:id>', methods=["DELETE"])
def delete_planet(id):
    exist = Planet.query.get(id)

    if not exist:
        return jsonify({"message": "Este Planeta no existe"}), 404

    db.session.delete(exist)
    db.session.commit()
    return jsonify({
        "message": "Plneta eliminado con exito",
        "planet": exist.serialize()
    }), 200


@app.route('/favorite/planets/<int:id>', methods=["POST"])
def add_favorite_planet(id):
    try:
        planet = Planet.query.get(id)
        if not planet:
            return jsonify({"message": "Planet no encontrado"}), 404
        exist = Favorites.query.filter_by(id_planet=id, id_user=1).first()
        if exist:
            return jsonify({"message": "already exist"}), 409
        favorite = Favorites(
                id_character=None,
                id_user=1,
                id_planet=id,
                name=planet.name,  # Asignar el nombre del Character
                tipo="planet"      # Asignar el tipo como "character"
            )
        db.session.add(favorite)
        db.session.commit()
        return jsonify(favorite.serialize()), 200
    except Exception as e:
        return jsonify({"message": "Error al agregar planeta a favoritos", "error": str(e)}), 500


@app.route('/favorite/planets/<int:id>', methods=["DELETE"])
def delete_favorite_peopl(id):
    exist = Favorites.query.filter_by(id_planet=id, id_user=1).first()
    
    if not exist:
        return jsonify({"message": "Este Favorito no existe"}), 404

    db.session.delete(exist)
    db.session.commit()
    return jsonify({
        "message": "Plneta Favorite eliminado con exito",
        "planet": exist.serialize()
    }), 200


@app.route('/favorite')
def get_all_favorites():
    favorites = Favorites.query.all()

    if not favorites:
        return jsonify({"message": "No hay favoritos"}), 404
    favorites_serialized = [fav.serialize() for fav in favorites]
    return jsonify(favorites_serialized), 200

@app.route('/users/<int:id>/favorites')
def get_all_favorites_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not exist"}), 404
    
    favorites = Favorites.query.filter_by(id_user=id).all()
    if not favorites:
        return jsonify({"message": "No hay favoritos"}), 404
    
    favorites_serialized = [fav.serialize() for fav in favorites]
    return jsonify(favorites_serialized), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
