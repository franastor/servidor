from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.database import get_db_connection
from mysql.connector import Error

class IncomeController:
    @staticmethod
    @jwt_required()
    def get_incomes():
        try:
            current_user = get_jwt_identity()
            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Obtener parámetros de filtro
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            category = request.args.get('category')
            
            # Construir la consulta base
            query = """
                SELECT i.*, u.nombre as nombre_usuario
                FROM incomes i
                JOIN usuarios u ON i.usuario = u.usuario
                WHERE 1=1
            """
            params = []
            
            # Añadir filtros si existen
            if start_date:
                query += " AND i.date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND i.date <= %s"
                params.append(end_date)
            if category:
                query += " AND i.category = %s"
                params.append(category)
            
            # Ordenar por fecha
            query += " ORDER BY i.date DESC"
            
            cursor.execute(query, tuple(params))
            incomes = cursor.fetchall()
            
            # Calcular total
            total = sum(income['amount'] for income in incomes)
            
            # Obtener categorías únicas
            cursor.execute("SELECT DISTINCT category FROM incomes ORDER BY category")
            categories = [row['category'] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()

            return jsonify({
                "incomes": incomes,
                "total": total,
                "categories": categories
            }), 200

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def create_income():
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            
            if not data or not all(k in data for k in ['amount', 'description', 'category']):
                return jsonify({"error": "Faltan campos requeridos"}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            # Crear ingreso
            cursor.execute("""
                INSERT INTO incomes (amount, description, category, date, usuario)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (data['amount'], data['description'], data['category'], current_user))
            
            income_id = cursor.lastrowid
            connection.commit()
            
            # Obtener el ingreso creado
            cursor.execute("""
                SELECT i.*, u.nombre as nombre_usuario
                FROM incomes i
                JOIN usuarios u ON i.usuario = u.usuario
                WHERE i.id = %s
            """, (income_id,))
            
            income = cursor.fetchone()
            cursor.close()
            connection.close()

            return jsonify(income), 201

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 