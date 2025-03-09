from flask import jsonify, request
from controllers.database import get_db_connection
from mysql.connector import Error
from datetime import datetime
import os
import logging
import re
from functools import wraps

logger = logging.getLogger(__name__)

def sanitize_input(value):
    """Sanitiza las entradas para prevenir inyección SQL"""
    if isinstance(value, str):
        # Elimina caracteres especiales y limita la longitud
        return re.sub(r'[^\w\s-]', '', value)[:100]
    return value

def validate_score_data(data):
    """Valida los datos de la puntuación"""
    if not isinstance(data.get('score'), (int, float)) or data['score'] < 0:
        return False, "La puntuación debe ser un número positivo"
    
    if not isinstance(data.get('game_duration'), (int, float)) or data['game_duration'] < 0:
        return False, "La duración del juego debe ser un número positivo"
    
    if not isinstance(data.get('interaction_count'), int) or data['interaction_count'] < 0:
        return False, "El contador de interacciones debe ser un número entero positivo"
    
    if not isinstance(data.get('name'), str) or len(data['name']) > 100:
        return False, "El nombre debe ser una cadena de texto de máximo 100 caracteres"
    
    if not isinstance(data.get('session_id'), str) or len(data['session_id']) > 100:
        return False, "El ID de sesión debe ser una cadena de texto de máximo 100 caracteres"
    
    return True, None

class ScoreController:
    @staticmethod
    def save_score():
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ['name', 'score', 'timestamp', 'session_id', 'game_duration', 'interaction_count']
            if not data or not all(field in data for field in required_fields):
                return jsonify({"error": "Faltan campos requeridos"}), 400

            # Validar datos
            is_valid, error_message = validate_score_data(data)
            if not is_valid:
                return jsonify({"error": error_message}), 400

            # Sanitizar entradas
            sanitized_data = {
                'name': sanitize_input(data['name']),
                'score': int(data['score']),
                'timestamp': int(data['timestamp']),
                'session_id': sanitize_input(data['session_id']),
                'game_duration': int(data['game_duration']),
                'interaction_count': int(data['interaction_count']),
                'game_version': sanitize_input(data.get('game_version', '')),
            }

            connection = get_db_connection()
            if not connection:
                logger.error("Error de conexión a la base de datos")
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor()
            
            try:
                # Insertar la puntuación con todos los campos
                query = """
                    INSERT INTO scores (
                        name, score, timestamp, session_id, is_valid, 
                        game_duration, interaction_count, game_version, 
                        platform, user_agent
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Obtener información del navegador
                user_agent = request.headers.get('User-Agent', '')[:255]  # Limitar longitud
                platform = request.headers.get('Sec-Ch-Ua-Platform', '')[:50]  # Limitar longitud
                
                values = (
                    sanitized_data['name'],
                    sanitized_data['score'],
                    sanitized_data['timestamp'],
                    sanitized_data['session_id'],
                    True,  # is_valid
                    sanitized_data['game_duration'],
                    sanitized_data['interaction_count'],
                    sanitized_data['game_version'],
                    platform,
                    user_agent
                )
                
                cursor.execute(query, values)
                connection.commit()
                last_id = cursor.lastrowid

                logger.info(f"Puntuación guardada exitosamente. ID: {last_id}")
                return jsonify({
                    "mensaje": "Puntuación guardada exitosamente",
                    "id": last_id
                }), 201

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            logger.error(f"Error en la base de datos: {str(e)}")
            return jsonify({"error": "Error en la base de datos"}), 500
        except Exception as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return jsonify({"error": "Error interno del servidor"}), 500

    @staticmethod
    def get_top_scores():
        try:
            connection = get_db_connection()
            if not connection:
                logger.error("Error de conexión a la base de datos")
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
            try:
                # Obtener las 10 mejores puntuaciones válidas
                query = """
                    SELECT 
                        name, score, timestamp, session_id, 
                        game_duration, interaction_count, game_version,
                        platform, user_agent, created_at
                    FROM scores 
                    WHERE is_valid = TRUE
                    ORDER BY score DESC 
                    LIMIT 10
                """
                cursor.execute(query)
                scores = cursor.fetchall()
                
                logger.info(f"Recuperadas {len(scores)} puntuaciones")
                return jsonify({
                    "mensaje": "Top 10 puntuaciones",
                    "scores": scores
                }), 200

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            logger.error(f"Error en la base de datos: {str(e)}")
            return jsonify({"error": "Error en la base de datos"}), 500
        except Exception as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return jsonify({"error": "Error interno del servidor"}), 500

    @staticmethod
    def delete_all_scores():
        try:
            connection = get_db_connection()
            if not connection:
                logger.error("Error de conexión a la base de datos")
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor()
            
            try:
                # Borrar todas las puntuaciones
                query = "DELETE FROM scores"
                cursor.execute(query)
                rows_deleted = cursor.rowcount
                connection.commit()

                logger.info(f"Eliminadas {rows_deleted} puntuaciones")
                return jsonify({
                    "mensaje": "Todas las puntuaciones han sido eliminadas",
                    "puntuaciones_eliminadas": rows_deleted
                }), 200

            finally:
                cursor.close()
                connection.close()

        except Error as e:
            logger.error(f"Error en la base de datos: {str(e)}")
            return jsonify({"error": "Error en la base de datos"}), 500
        except Exception as e:
            logger.error(f"Error interno del servidor: {str(e)}")
            return jsonify({"error": "Error interno del servidor"}), 500 