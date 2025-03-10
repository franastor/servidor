from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from controllers.database import get_db_connection

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_user = get_jwt_identity()
            if not current_user:
                return jsonify({'message': 'Usuario no autenticado'}), 401

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Verificar si el usuario es administrador
            cursor.execute("""
                SELECT r.nombre as rol
                FROM usuarios u
                JOIN roles r ON u.rol_id = r.id
                WHERE u.usuario = %s
            """, (current_user,))
            
            user_role = cursor.fetchone()
            if not user_role or user_role['rol'] != 'admin':
                return jsonify({'message': 'Se requieren permisos de administrador'}), 403

            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500

    return decorated_function 