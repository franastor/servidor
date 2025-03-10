from flask import request, jsonify
from controllers.database import get_db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime
from mysql.connector import Error

class LogController:
    @staticmethod
    def log_action(accion: str, tabla: str, usuario: str, detalles: dict = None):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener información del cliente
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            # Convertir detalles a JSON si existen
            detalles_json = json.dumps(detalles) if detalles else None
            
            # Insertar el log
            cursor.execute("""
                INSERT INTO logs (accion, tabla, usuario, ip, dispositivo, detalles)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (accion, tabla, usuario, ip, user_agent, detalles_json))
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Error as e:
            print(f"Error al registrar log: {str(e)}")
            if connection:
                connection.close()
    
    @staticmethod
    @jwt_required()
    def get_logs():
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener parámetros de filtrado y ordenamiento
            filters = request.args.to_dict()
            sort_by = filters.pop('sort_by', 'created_at')
            sort_order = filters.pop('sort_order', 'DESC')
            page = int(filters.pop('page', 1))
            per_page = int(filters.pop('per_page', 10))
            
            # Validar el campo de ordenamiento
            valid_fields = ['id', 'accion', 'tabla', 'usuario', 'ip', 'created_at']
            if sort_by not in valid_fields:
                sort_by = 'created_at'
            
            # Validar el orden
            if sort_order.upper() not in ['ASC', 'DESC']:
                sort_order = 'DESC'
            
            # Construir la consulta base
            query = """
                SELECT *
                FROM logs
                WHERE 1=1
            """
            params = []
            
            # Aplicar filtros si existen
            for field in filters:
                if field in valid_fields:
                    query += f" AND {field} LIKE %s"
                    params.append(f"%{filters[field]}%")
                elif field == 'fecha_inicio':
                    query += " AND created_at >= %s"
                    params.append(filters[field])
                elif field == 'fecha_fin':
                    query += " AND created_at <= %s"
                    params.append(filters[field])
            
            # Obtener el total de registros
            count_query = f"SELECT COUNT(*) as total FROM logs WHERE 1=1"
            count_params = []
            for field in filters:
                if field in valid_fields:
                    count_query += f" AND {field} LIKE %s"
                    count_params.append(f"%{filters[field]}%")
                elif field == 'fecha_inicio':
                    count_query += " AND created_at >= %s"
                    count_params.append(filters[field])
                elif field == 'fecha_fin':
                    count_query += " AND created_at <= %s"
                    count_params.append(filters[field])
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            # Agregar ordenamiento y paginación
            query += f" ORDER BY {sort_by} {sort_order}"
            offset = (page - 1) * per_page
            query += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            # Ejecutar la consulta
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            # Obtener valores únicos para los filtros
            cursor.execute("SELECT DISTINCT accion FROM logs ORDER BY accion")
            acciones = [row['accion'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT tabla FROM logs ORDER BY tabla")
            tablas = [row['tabla'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT usuario FROM logs ORDER BY usuario")
            usuarios = [row['usuario'] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'logs': logs,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
                'filters': {
                    'acciones': acciones,
                    'tablas': tablas,
                    'usuarios': usuarios
                }
            }), 200
            
        except Error as e:
            print(f"Error al obtener logs: {str(e)}")
            if connection:
                connection.close()
            return jsonify({
                'message': 'Error interno del servidor',
                'error': str(e)
            }), 500 