from flask import jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error
import io
import os
from utils.auth import admin_required
from io import BytesIO

class ExpenseController:
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB en bytes

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ExpenseController.ALLOWED_EXTENSIONS

    @staticmethod
    @jwt_required()
    def get_expenses():
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
            category = request.args.get('category')
            usuario = request.args.get('usuario')

            # Construir la consulta base
            query = """
                SELECT e.id, e.amount, e.description, e.category, e.date, 
                       u.nombre as nombre_usuario,
                       CASE WHEN e.invoice_name IS NOT NULL THEN true ELSE false END as has_invoice,
                       e.invoice_name,
                       e.invoice_type
                FROM expenses e
                JOIN usuarios u ON u.id = e.user_id
                WHERE 1=1
            """
            params = []

            # Aplicar filtros si están presentes
            if start_date:
                query += " AND e.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND e.date <= %s"
                params.append(end_date)
            if category:
                query += " AND e.category = %s"
                params.append(category)
            if usuario:
                query += " AND u.nombre = %s"
                params.append(usuario)

            # Ordenar por fecha descendente
            query += " ORDER BY e.date DESC"

            # Ejecutar la consulta
            cursor.execute(query, params)
            expenses = cursor.fetchall()

            # Obtener el total
            total = sum(expense['amount'] for expense in expenses)

            # Obtener categorías únicas
            cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
            categories = [row['category'] for row in cursor.fetchall()]

            return jsonify({
                'expenses': expenses,
                'total': total,
                'categories': categories
            }), 200

        except Exception as e:
            print(f"Error en get_expenses: {str(e)}")
            return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    def create_expense():
        connection = None
        cursor = None
        try:
            current_user = get_jwt_identity()
            
            # Obtener datos del formulario
            amount = request.form.get('amount')
            category = request.form.get('category')
            description = request.form.get('description')
            invoice = request.files.get('invoice')

            if not all([amount, category, description]):
                return jsonify({'error': 'Faltan campos requeridos'}), 400

            # Validar el archivo si se proporciona
            invoice_data = None
            invoice_name = None
            invoice_type = None
            if invoice:
                # Validar el tipo de archivo
                if not ExpenseController.allowed_file(invoice.filename):
                    return jsonify({'error': 'Tipo de archivo no permitido. Solo se permiten PDF y JPG/JPEG'}), 400
                
                # Validar el tamaño del archivo
                invoice.seek(0, os.SEEK_END)
                size = invoice.tell()
                if size > ExpenseController.MAX_FILE_SIZE:
                    return jsonify({'error': 'El archivo es demasiado grande. El tamaño máximo es 2 MB'}), 400
                
                invoice.seek(0)
                invoice_data = invoice.read()
                invoice_name = invoice.filename
                invoice_type = invoice.filename.rsplit('.', 1)[1].lower()

            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)

            # Obtener el ID del usuario
            cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (current_user,))
            user_result = cursor.fetchone()
            if not user_result:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            # Insertar el gasto
            cursor.execute("""
                INSERT INTO expenses (amount, category, description, user_id, invoice, invoice_name, invoice_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (float(amount), category, description, user_result['id'], invoice_data, invoice_name, invoice_type))

            connection.commit()

            # Obtener el gasto recién creado
            cursor.execute("""
                SELECT e.id, e.amount, e.category, e.description, e.date, 
                       u.nombre as nombre_usuario,
                       CASE WHEN e.invoice_name IS NOT NULL THEN true ELSE false END as has_invoice,
                       e.invoice_name,
                       e.invoice_type
                FROM expenses e
                JOIN usuarios u ON u.id = e.user_id
                WHERE e.id = LAST_INSERT_ID()
            """)

            new_expense = cursor.fetchone()

            return jsonify({
                'message': 'Gasto creado exitosamente',
                'expense': new_expense
            }), 201

        except Exception as e:
            print(f"Error al crear gasto: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @staticmethod
    @jwt_required()
    def get_invoice(expense_id):
        try:
            current_user = get_jwt_identity()
            connection = get_db_connection()
            if not connection:
                return jsonify({'error': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)

            # Verificar que el gasto existe y pertenece al usuario
            cursor.execute("""
                SELECT e.invoice, e.invoice_name, e.invoice_type
                FROM expenses e
                JOIN usuarios u ON e.user_id = u.id
                WHERE e.id = %s AND u.usuario = %s
            """, (expense_id, current_user))

            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if not result or not result['invoice']:
                return jsonify({'error': 'Factura no encontrada'}), 404

            # Crear un objeto BytesIO con los datos del archivo
            file_data = BytesIO(result['invoice'])
            
            # Determinar el tipo MIME basado en el tipo de archivo
            mime_type = 'application/pdf' if result['invoice_type'] == 'pdf' else 'image/jpeg'

            return send_file(
                file_data,
                mimetype=mime_type,
                as_attachment=True,
                download_name=result['invoice_name']
            )

        except Exception as e:
            print(f"Error al obtener factura: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @staticmethod
    @jwt_required()
    @admin_required
    def delete_expense(expense_id):
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            if not connection:
                return jsonify({'message': 'Error de conexión a la base de datos'}), 500

            cursor = connection.cursor(dictionary=True)

            # Verificar que el gasto existe
            cursor.execute("SELECT id FROM expenses WHERE id = %s", (expense_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Gasto no encontrado'}), 404

            # Eliminar el gasto
            cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            connection.commit()

            return jsonify({
                'message': 'Gasto eliminado exitosamente',
                'expense_id': expense_id
            }), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close() 