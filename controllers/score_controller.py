from flask import jsonify, request
from controllers.database import get_db_connection
from mysql.connector import Error
from datetime import datetime
import os
from functools import wraps

class ScoreController:
    @staticmethod
    def save_score():
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ['name', 'score', 'timestamp', 'session_id', 'game_duration', 'interaction_count']
            if not data or not all(field in data for field in required_fields):
                return jsonify({"error": "Faltan campos requeridos"}), 400

            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor()
            
            # Insertar la puntuación con todos los campos
            query = """
                INSERT INTO scores (
                    name, score, timestamp, session_id, is_valid, 
                    game_duration, interaction_count, game_version, 
                    platform, user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Obtener información del navegador
            user_agent = request.headers.get('User-Agent', '')
            platform = request.headers.get('Sec-Ch-Ua-Platform', '')
            
            values = (
                data['name'],
                data['score'],
                data['timestamp'],
                data['session_id'],
                data.get('is_valid', True),
                data['game_duration'],
                data['interaction_count'],
                data.get('game_version'),
                platform,
                user_agent
            )
            
            cursor.execute(query, values)
            connection.commit()
            cursor.close()
            connection.close()

            return jsonify({
                "mensaje": "Puntuación guardada exitosamente",
                "id": cursor.lastrowid
            }), 201

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

    @staticmethod
    def get_top_scores():
        try:
            connection = get_db_connection()
            if not connection:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            cursor = connection.cursor(dictionary=True)
            
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
            
            cursor.close()
            connection.close()

            return jsonify({
                "mensaje": "Top 10 puntuaciones",
                "scores": scores
            }), 200

        except Error as e:
            return jsonify({"error": f"Error en la base de datos: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 