from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from dotenv import load_dotenv
import os
from controllers.basic_controller import BasicController
from controllers.auth_controller import AuthController
from controllers.docs_controller import DocsController
from controllers.score_controller import ScoreController
from controllers.database import get_db_connection
from datetime import datetime, timedelta
import logging
import mysql.connector
from mysql.connector import Error

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(override=True)

# Verificar que las variables de entorno se cargaron correctamente
print("MASTER_TOKEN:", os.getenv('MASTER_TOKEN'))
print("JWT_SECRET_KEY:", os.getenv('JWT_SECRET_KEY'))

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '1234')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

# Rutas públicas
@app.route('/')
def root():
    return jsonify({
        "message": "Nada que ver aquí... 👀",
        "status": "404"
    }), 404

@app.route('/live')
def health_check():
    return jsonify({
        "status": "alive",
        "message": "¡El servidor está funcionando! 🚀",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/endpoints')
def list_endpoints():
    endpoints = {
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Endpoint raíz"
            },
            {
                "path": "/live",
                "method": "GET",
                "description": "Health check del servidor"
            },
            {
                "path": "/endpoints",
                "method": "GET",
                "description": "Lista todos los endpoints disponibles"
            },
            {
                "path": "/login",
                "method": "POST",
                "description": "Autenticación de usuario"
            },
            {
                "path": "/inicio",
                "method": "GET",
                "description": "Mensaje de bienvenida"
            },
            {
                "path": "/fin",
                "method": "GET",
                "description": "Mensaje de despedida"
            },
            {
                "path": "/docs",
                "method": "GET",
                "description": "Documentación de la API"
            },
            {
                "path": "/scores",
                "method": "POST",
                "description": "Guarda una nueva puntuación"
            },
            {
                "path": "/scores/top",
                "method": "GET",
                "description": "Obtiene las 10 mejores puntuaciones"
            }
        ]
    }
    return jsonify(endpoints), 200

# Rutas de la API
app.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
app.add_url_rule('/docs', 'docs', DocsController.get_docs, methods=['GET'])

# Rutas de puntuaciones
app.add_url_rule('/scores', 'save_score', ScoreController.save_score, methods=['POST'])
app.add_url_rule('/scores/top', 'get_top_scores', ScoreController.get_top_scores, methods=['GET'])

# Rutas protegidas
app.add_url_rule('/inicio', 'inicio', BasicController.inicio, methods=['GET'])
app.add_url_rule('/fin', 'fin', BasicController.fin, methods=['GET'])

def verificar_conexion_db():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            print("\033[92m✓ Conexión exitosa a la base de datos MySQL\033[0m")
            conn.close()
            return True
    except Exception as e:
        print("\033[91m✗ Error al conectar a la base de datos MySQL:", str(e), "\033[0m")
        return False

if __name__ == '__main__':
    print("\nIniciando servidor Flask...")
    if verificar_conexion_db():
        print("\033[92m✓ Servidor iniciado correctamente en http://127.0.0.1:5001\033[0m")
    else:
        print("\033[91m✗ Servidor iniciado con errores de conexión a la base de datos\033[0m")
    app.run(debug=True, port=5001) 