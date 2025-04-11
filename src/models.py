from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=True)

    # relations
    fav = relationship('Favorites', backref='user')
    # serialize

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "favorites": [fav.serialize() for fav in self.fav]
        }


class Character(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    specie: Mapped[str] = mapped_column(String(120), nullable=True)

    # serialize
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "specie": self.specie
        }


class Planet(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # serialize

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Favorites(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True, default='Unknown')
    tipo: Mapped[str] = mapped_column(String(50), nullable=True, default='Unknown')
    id_user: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    id_planet: Mapped[int] = mapped_column(
        ForeignKey('planet.id'), nullable=True)
    id_character: Mapped[int] = mapped_column(
        ForeignKey('character.id'), nullable=True)

    # relations
    character = relationship('Character', backref='favorites')
    planet = relationship('Planet', backref='favorites')
    # serialize

    def serialize(self):
        if self.id_character:
            return {
                "id": self.id,
                "tipo": "character",
                "name": self.character.name,
                "id_user": self.id_user
            }
        elif self.id_planet:
            return {
                "id": self.id,
                "tipo": "planet",
                "name": self.planet.name,
                "id_user": self.id_user
            }
        else:
            return {
                "id": self.id,
                "tipo": "unknown",
                "id_user": self.id_user
            }

    def full_serialize(self):
        data_favorite = {
            "id": self.id,
            "id_user": self.id_user
        }

        if self.id_planet:
            data_favorite['item'] = self.planet.serialize()
        elif self.id_character:
            data_favorite['item'] = self.character.serialize()

        return data_favorite
