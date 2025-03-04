from flask import jsonify
from flask_jwt_extended import jwt_required

class BasicController:
    @staticmethod
    @jwt_required()
    def inicio():
        return jsonify({"mensaje": "Hola"})

    @staticmethod
    @jwt_required()
    def fin():
        return jsonify({"mensaje": "Adios"}) 