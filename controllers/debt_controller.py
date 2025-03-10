from flask import jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error
import io
from utils.auth import admin_required
from controllers.log_controller import LogController

class DebtController:
    @staticmethod
    @jwt_required()
    def get_debts():
        connection = None
        cursor = None
        try:
            current_user = get_jwt_identity()
            if not current_user:
                return jsonify({'message': 'Usuario no autenticado'}), 401

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)

            # Obtener los parámetros de filtro
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            usuario = request.args.get('usuario')
            deudor = request.args.get('deudor')

            # Construir la consulta base
            query = """
                SELECT d.id, d.amount, d.description, d.date, d.isPaid, 
                       u.nombre as nombre_usuario, db.nombre as nombre_deudor
                FROM debts d
                JOIN usuarios u ON u.id = d.user_id
                JOIN debtors db ON db.id = d.debtor_id
                WHERE 1=1
            """
            params = []

            # Aplicar filtros si están presentes
            if start_date:
                query += " AND d.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND d.date <= %s"
                params.append(end_date)
            if usuario:
                query += " AND u.nombre = %s"
                params.append(usuario)
            if deudor:
                query += " AND db.nombre = %s"
                params.append(deudor)

            # Ordenar por fecha descendente
            query += " ORDER BY d.date DESC"

            print("Query:", query)  # Debug
            print("Params:", params)  # Debug

            # Ejecutar la consulta
            cursor.execute(query, params)
            debts = cursor.fetchall()

            print("Debts:", debts)  # Debug

            # Obtener el total
            total = sum(debt['amount'] for debt in debts)

            # Obtener usuarios únicos
            cursor.execute("SELECT DISTINCT nombre FROM usuarios ORDER BY nombre")
            users = [row['nombre'] for row in cursor.fetchall()]

            return jsonify({
                'debts': debts,
                'total': total,
                'users': users
            }), 200

        except Exception as e:
            print(f"Error en get_debts: {str(e)}")
            return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    def create_debt():
        connection = None
        cursor = None
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data or not all(k in data for k in ['amount', 'description', 'debtor_id']):
                return jsonify({'error': 'Faltan campos requeridos'}), 400
            
            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Obtener el ID del usuario
            cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (current_user,))
            user_result = cursor.fetchone()
            if not user_result:
                return jsonify({'error': 'Usuario no encontrado'}), 404
            user_id = user_result['id']
            
            # Verificar si el deudor existe
            cursor.execute('SELECT id FROM debtors WHERE id = %s', (data['debtor_id'],))
            if not cursor.fetchone():
                return jsonify({'error': 'Deudor no encontrado'}), 404
            
            cursor.execute("""
                INSERT INTO debts (amount, description, user_id, debtor_id)
                VALUES (%s, %s, %s, %s)
            """, (data['amount'], data['description'], user_id, data['debtor_id']))
            
            connection.commit()
            
            # Obtener la deuda recién creada
            cursor.execute("""
                SELECT d.id, d.amount, d.description, d.date, d.isPaid,
                       u.nombre as nombre_usuario, db.nombre as nombre_deudor
                FROM debts d
                JOIN usuarios u ON u.id = d.user_id
                JOIN debtors db ON db.id = d.debtor_id
                WHERE d.id = LAST_INSERT_ID()
            """)
            
            debt = cursor.fetchone()
            
            return jsonify({
                'message': 'Deuda creada exitosamente',
                'debt': debt
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    def update_debt(debt_id):
        connection = None
        cursor = None
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No hay datos para actualizar"}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Obtener el ID del usuario
            cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (current_user,))
            user_result = cursor.fetchone()
            if not user_result:
                return jsonify({"error": "Usuario no encontrado"}), 404
            user_id = user_result['id']
            
            # Verificar permisos
            cursor.execute("""
                SELECT COUNT(*) as tiene_permiso
                FROM usuarios u
                JOIN roles_permisos rp ON u.rol_id = rp.rol_id
                JOIN permisos p ON rp.permiso_id = p.id
                WHERE u.id = %s AND p.nombre = 'editar_deudas'
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result or result['tiene_permiso'] == 0:
                return jsonify({"error": "No tienes permiso para editar deudas"}), 403

            # Verificar que la deuda existe y pertenece al usuario
            cursor.execute("""
                SELECT id FROM debts
                WHERE id = %s AND user_id = %s
            """, (debt_id, user_id))
            
            if not cursor.fetchone():
                return jsonify({"error": "Deuda no encontrada o no tienes permiso para editarla"}), 404

            # Actualizar deuda
            update_fields = []
            update_values = []
            
            if 'amount' in data:
                update_fields.append("amount = %s")
                update_values.append(data['amount'])
            if 'debtor_id' in data:
                update_fields.append("debtor_id = %s")
                update_values.append(data['debtor_id'])
            if 'description' in data:
                update_fields.append("description = %s")
                update_values.append(data['description'])
            if 'isPaid' in data:
                update_fields.append("isPaid = %s")
                update_values.append(data['isPaid'])
            
            if not update_fields:
                return jsonify({"error": "No hay campos para actualizar"}), 400
            
            update_values.extend([debt_id, user_id])
            cursor.execute(f"""
                UPDATE debts
                SET {", ".join(update_fields)}
                WHERE id = %s AND user_id = %s
            """, tuple(update_values))
            
            connection.commit()
            
            # Obtener la deuda actualizada
            cursor.execute("""
                SELECT d.id, d.amount, d.description, d.date, d.isPaid,
                       u.nombre as nombre_usuario, db.nombre as nombre_deudor
                FROM debts d
                JOIN usuarios u ON u.id = d.user_id
                JOIN debtors db ON db.id = d.debtor_id
                WHERE d.id = %s
            """, (debt_id,))
            
            debt = cursor.fetchone()
            return jsonify(debt), 200

        except Error as e:
            if connection:
                connection.rollback()
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            if connection:
                connection.rollback()
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    @admin_required
    def delete_debt(debt_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Verificar que la deuda existe y pertenece al usuario
            user_id = get_jwt_identity()
            cursor.execute("""
                SELECT id FROM debts
                WHERE id = %s AND user_id = %s
            """, (debt_id, user_id))
            
            debt = cursor.fetchone()
            if not debt:
                return jsonify({
                    'message': 'Deuda no encontrada o no tienes permiso para eliminarla'
                }), 404
            
            # Eliminar la deuda
            cursor.execute("DELETE FROM debts WHERE id = %s", (debt_id,))
            connection.commit()
            
            # Registrar la acción en los logs
            LogController.log_action(
                accion='eliminar',
                tabla='debts',
                usuario=user_id,
                detalles={'debt_id': debt_id}
            )
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'message': 'Deuda eliminada exitosamente'
            }), 200
            
        except Error as e:
            print(f"Error al eliminar deuda: {str(e)}")
            if connection:
                connection.close()
            return jsonify({
                'message': 'Error interno del servidor',
                'error': str(e)
            }), 500

    @staticmethod
    @jwt_required()
    def get_debt_file(debt_id):
        connection = None
        cursor = None
        try:
            current_user = get_jwt_identity()
            if not current_user:
                return jsonify({'message': 'Usuario no autenticado'}), 401

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Verificar que la deuda existe y pertenece al usuario
            cursor.execute("""
                SELECT id FROM debts
                WHERE id = %s AND user_id = %s
            """, (debt_id, current_user))
            
            if not cursor.fetchone():
                return jsonify({"error": "Deuda no encontrada o no tienes permiso para acceder a ella"}), 404

            # Obtener el archivo de la deuda
            cursor.execute("""
                SELECT file_content FROM debts
                WHERE id = %s
            """, (debt_id,))
            
            file_content = cursor.fetchone()['file_content']
            
            if not file_content:
                return jsonify({'message': 'Archivo no encontrado'}), 404

            return send_file(io.BytesIO(file_content), mimetype='application/pdf'), 200

        except Exception as e:
            print(f"Error en get_debt_file: {str(e)}")
            return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close() 