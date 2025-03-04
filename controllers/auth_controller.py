from flask import jsonify, request
from flask_jwt_extended import create_access_token
from datetime import timedelta
from controllers.database import get_db_connection
from mysql.connector import Error

class AuthController:
    @staticmethod
    def login():
        try:
            data = request.get_json()
            
            if not data or 'usuario' not in data or 'password' not in data:
                return jsonify({"error": "Se requieren usuario y contraseña"}), 400

            # Obtener conexión a la base de datos
            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Usar parámetros para prevenir inyección SQL
            query = "SELECT * FROM usuarios WHERE usuario = %s AND password = %s"
            cursor.execute(query, (data['usuario'], data['password']))
            
            user = cursor.fetchone()
            
            cursor.close()
            connection.close()

            if user:
                # Crear token JWT con expiración de 1 hora
                access_token = create_access_token(
                    identity=user['usuario'],
                    expires_delta=timedelta(hours=1)
                )
                return jsonify({
                    "mensaje": "Login exitoso",
                    "token": access_token,
                    "usuario": user['usuario']
                }), 200
            else:
                return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 