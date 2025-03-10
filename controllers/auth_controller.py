from flask import jsonify, request
from flask_jwt_extended import create_access_token
from datetime import timedelta
from controllers.database import get_db_connection
from mysql.connector import Error
from controllers.log_controller import LogController
import logging
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

class AuthController:
    @staticmethod
    def login():
        try:
            data = request.get_json()
            
            if not data:
                logger.error("No se recibieron datos en el body")
                return jsonify({"error": "No se recibieron datos"}), 400
                
            # Aceptar tanto 'usuario' como 'username'
            usuario = data.get('usuario') or data.get('username')
            password = data.get('password')

            if not usuario or not password:
                logger.error("Faltan campos requeridos en la petición")
                return jsonify({"error": "Se requieren usuario y contraseña"}), 400

            logger.info(f"Intento de login para usuario: {usuario}")

            connection = get_db_connection()
            if not connection:
                logger.error("No se pudo establecer conexión con la base de datos")
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            try:
                # Obtener usuario con su rol y permisos
                cursor.execute("""
                    SELECT 
                        u.id, 
                        u.usuario, 
                        u.password, 
                        u.nombre, 
                        u.email,
                        u.activo, 
                        r.id as rol_id, 
                        r.nombre as rol,
                        r.descripcion as rol_descripcion
                    FROM usuarios u
                    LEFT JOIN roles r ON r.id = u.rol_id
                    WHERE u.usuario = %s
                """, (usuario,))
                
                user = cursor.fetchone()
                if not user:
                    logger.warning(f"Usuario no encontrado: {usuario}")
                    return jsonify({"error": "Usuario o contraseña incorrectos"}), 401
                
                if not check_password_hash(user['password'], password):
                    logger.warning(f"Contraseña incorrecta para usuario: {usuario}")
                    return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

                if not user['activo']:
                    logger.warning(f"Usuario bloqueado: {usuario}")
                    return jsonify({"error": "Tu cuenta está bloqueada. Contacta con el administrador."}), 401

                # Obtener permisos del usuario
                cursor.execute("""
                    SELECT p.nombre as permiso, p.descripcion
                    FROM roles_permisos rp 
                    JOIN permisos p ON rp.permiso_id = p.id
                    WHERE rp.rol_id = %s
                """, (user['rol_id'],))
                
                permisos = cursor.fetchall()
                logger.info(f"Permisos encontrados para {usuario}: {permisos}")

                # Crear token JWT
                access_token = create_access_token(
                    identity=user['usuario'],
                    expires_delta=timedelta(hours=1)
                )
                
                # Registrar login exitoso
                LogController.log_action(
                    accion='login_exitoso',
                    tabla='usuarios',
                    usuario=usuario,
                    detalles=None
                )
                
                return jsonify({
                    "mensaje": "Login exitoso",
                    "token": access_token,
                    "id": user['id'],
                    "usuario": user['usuario'],
                    "nombre": user['nombre'],
                    "email": user['email'] or "",
                    "role": user['rol'],
                    "rol_descripcion": user['rol_descripcion'],
                    "activo": user['activo'],
                    "permisos": [{"nombre": p["permiso"], "descripcion": p["descripcion"]} for p in permisos]
                }), 200

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            logger.error(f"Error de MySQL: {str(e)}")
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 