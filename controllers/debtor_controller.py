from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error

class DebtorController:
    @staticmethod
    @jwt_required()
    def get_debtors():
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, nombre, email, telefono, fecha_creacion
                FROM debtors
                ORDER BY nombre
            """)
            
            debtors = cursor.fetchall()
            
            return jsonify({'debtors': debtors}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    def create_debtor():
        connection = None
        cursor = None
        try:
            data = request.get_json()
            
            if not data or not data.get('nombre'):
                return jsonify({'error': 'Se requiere al menos el nombre del deudor'}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                INSERT INTO debtors (nombre, email, telefono)
                VALUES (%s, %s, %s)
            """, (data.get('nombre'), data.get('email'), data.get('telefono')))
            
            connection.commit()
            
            # Obtener el deudor recién creado
            cursor.execute("""
                SELECT id, nombre, email, telefono, fecha_creacion
                FROM debtors
                WHERE id = LAST_INSERT_ID()
            """)
            
            new_debtor = cursor.fetchone()
            
            return jsonify({
                'message': 'Deudor creado exitosamente',
                'debtor': new_debtor
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
    def update_debtor(debtor_id):
        connection = None
        cursor = None
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No hay datos para actualizar'}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Verificar que el deudor existe
            cursor.execute("SELECT id FROM debtors WHERE id = %s", (debtor_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Deudor no encontrado'}), 404

            # Actualizar deudor
            update_fields = []
            update_values = []
            
            if 'nombre' in data:
                update_fields.append("nombre = %s")
                update_values.append(data['nombre'])
            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])
            if 'telefono' in data:
                update_fields.append("telefono = %s")
                update_values.append(data['telefono'])
            
            if not update_fields:
                return jsonify({'error': 'No hay campos válidos para actualizar'}), 400
            
            update_values.append(debtor_id)
            query = f"""
                UPDATE debtors
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            cursor.execute(query, tuple(update_values))
            connection.commit()
            
            # Obtener el deudor actualizado
            cursor.execute("""
                SELECT id, nombre, email, telefono, fecha_creacion
                FROM debtors
                WHERE id = %s
            """, (debtor_id,))
            
            updated_debtor = cursor.fetchone()
            
            return jsonify({
                'message': 'Deudor actualizado exitosamente',
                'debtor': updated_debtor
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close() 