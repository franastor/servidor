from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error

class RoleController:
    @staticmethod
    @jwt_required()
    def get_roles():
        try:
            current_user = get_jwt_identity()
            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

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
                return jsonify({"error": "No tienes permiso para ver roles"}), 403

            # Obtener roles con sus permisos
            cursor.execute("""
                SELECT r.id, r.nombre, GROUP_CONCAT(p.nombre) as permisos
                FROM roles r
                LEFT JOIN roles_permisos rp ON r.id = rp.rol_id
                LEFT JOIN permisos p ON rp.permiso_id = p.id
                GROUP BY r.id, r.nombre
            """)
            
            roles = cursor.fetchall()
            
            # Obtener todos los permisos disponibles
            cursor.execute("SELECT id, nombre FROM permisos")
            permisos = cursor.fetchall()
            
            cursor.close()
            connection.close()

            return jsonify({
                "roles": roles,
                "permisos_disponibles": permisos
            }), 200

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def create_role():
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'nombre' not in data or 'permisos' not in data:
                return jsonify({"error": "Faltan campos requeridos"}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

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
                return jsonify({"error": "No tienes permiso para crear roles"}), 403

            # Crear rol
            cursor.execute("""
                INSERT INTO roles (nombre)
                VALUES (%s)
            """, (data['nombre'],))
            
            rol_id = cursor.lastrowid
            
            # Asignar permisos al rol
            for permiso_id in data['permisos']:
                cursor.execute("""
                    INSERT INTO roles_permisos (rol_id, permiso_id)
                    VALUES (%s, %s)
                """, (rol_id, permiso_id))
            
            connection.commit()
            
            # Obtener el rol creado con sus permisos
            cursor.execute("""
                SELECT r.id, r.nombre, GROUP_CONCAT(p.nombre) as permisos
                FROM roles r
                LEFT JOIN roles_permisos rp ON r.id = rp.rol_id
                LEFT JOIN permisos p ON rp.permiso_id = p.id
                WHERE r.id = %s
                GROUP BY r.id, r.nombre
            """, (rol_id,))
            
            role = cursor.fetchone()
            cursor.close()
            connection.close()

            return jsonify(role), 201

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def update_role(role_id):
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'permisos' not in data:
                return jsonify({"error": "Faltan campos requeridos"}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

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
                return jsonify({"error": "No tienes permiso para actualizar roles"}), 403

            # Verificar que el rol existe
            cursor.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Rol no encontrado"}), 404

            # Eliminar permisos actuales
            cursor.execute("DELETE FROM roles_permisos WHERE rol_id = %s", (role_id,))
            
            # Asignar nuevos permisos
            for permiso_id in data['permisos']:
                cursor.execute("""
                    INSERT INTO roles_permisos (rol_id, permiso_id)
                    VALUES (%s, %s)
                """, (role_id, permiso_id))
            
            connection.commit()
            
            # Obtener el rol actualizado con sus permisos
            cursor.execute("""
                SELECT r.id, r.nombre, GROUP_CONCAT(p.nombre) as permisos
                FROM roles r
                LEFT JOIN roles_permisos rp ON r.id = rp.rol_id
                LEFT JOIN permisos p ON rp.permiso_id = p.id
                WHERE r.id = %s
                GROUP BY r.id, r.nombre
            """, (role_id,))
            
            role = cursor.fetchone()
            cursor.close()
            connection.close()

            return jsonify(role), 200

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def delete_role(role_id):
        try:
            current_user = get_jwt_identity()
            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

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
                return jsonify({"error": "No tienes permiso para eliminar roles"}), 403

            # Verificar que el rol existe y no es el rol de administrador
            cursor.execute("SELECT nombre FROM roles WHERE id = %s", (role_id,))
            role = cursor.fetchone()
            
            if not role:
                return jsonify({"error": "Rol no encontrado"}), 404
                
            if role['nombre'] == 'admin':
                return jsonify({"error": "No se puede eliminar el rol de administrador"}), 403

            # Verificar si hay usuarios usando este rol
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE rol_id = %s", (role_id,))
            user_count = cursor.fetchone()['count']
            
            if user_count > 0:
                return jsonify({"error": "No se puede eliminar el rol porque hay usuarios asignados a él"}), 400

            # Eliminar el rol (la eliminación en cascada se encargará de los permisos)
            cursor.execute("DELETE FROM roles WHERE id = %s", (role_id,))
            connection.commit()
            
            cursor.close()
            connection.close()

            return jsonify({"mensaje": "Rol eliminado correctamente"}), 200

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 