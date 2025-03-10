from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from dotenv import load_dotenv
import os
from controllers.basic_controller import BasicController
from controllers.auth_controller import AuthController
from controllers.docs_controller import DocsController
from controllers.score_controller import ScoreController
from controllers.user_controller import UserController, get_user_permissions, create_user, update_user, reset_password, change_password
from controllers.expense_controller import ExpenseController
from controllers.debt_controller import DebtController
from controllers.database import get_db_connection
from datetime import datetime, timedelta
import logging
import mysql.connector
from mysql.connector import Error
from controllers.role_controller import RoleController
from controllers.email_controller import EmailController
from controllers.debtor_controller import DebtorController
from controllers.log_controller import LogController

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(override=True)

# Verificar que las variables de entorno se cargaron correctamente
logger.info("Cargando configuración...")

app = Flask(__name__)

# Configuración de seguridad
app.config['JSON_SORT_KEYS'] = False  # Previene ataques de timing
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limita el tamaño de las peticiones a 16MB

# Configuración de CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Content-Disposition"],
        "max_age": 600,
        "supports_credentials": True
    }
})

# Configuración de JWT con mejoras de seguridad
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '1234')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
jwt = JWTManager(app)

# Headers de seguridad
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' *; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Content-Disposition'
    return response

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
                "path": "/users",
                "method": "GET",
                "description": "Obtiene la lista de usuarios"
            },
            {
                "path": "/users",
                "method": "POST",
                "description": "Crea un nuevo usuario"
            },
            {
                "path": "/users/permissions",
                "method": "GET",
                "description": "Obtiene los permisos del usuario actual"
            },
            {
                "path": "/users/<int:user_id>/toggle-status",
                "method": "POST",
                "description": "Activa/desactiva un usuario"
            },
            {
                "path": "/users/<int:user_id>",
                "method": "PUT",
                "description": "Actualiza la información de un usuario"
            },
            {
                "path": "/users/<int:user_id>/reset-password",
                "method": "POST",
                "description": "Restablece la contraseña de un usuario y envía email"
            },
            {
                "path": "/expenses",
                "method": "GET",
                "description": "Obtiene la lista de gastos"
            },
            {
                "path": "/expenses",
                "method": "POST",
                "description": "Crea un nuevo gasto"
            },
            {
                "path": "/expenses/<int:expense_id>",
                "method": "DELETE",
                "description": "Elimina un gasto"
            },
            {
                "path": "/expenses/<int:expense_id>/invoice",
                "method": "GET",
                "description": "Obtiene la factura de un gasto"
            },
            {
                "path": "/debts",
                "method": "GET",
                "description": "Obtiene la lista de deudas"
            },
            {
                "path": "/debts",
                "method": "POST",
                "description": "Crea una nueva deuda"
            },
            {
                "path": "/debts/<int:debt_id>",
                "method": "PATCH",
                "description": "Actualiza una deuda"
            },
            {
                "path": "/debts/<int:debt_id>",
                "method": "DELETE",
                "description": "Elimina una deuda"
            },
            {
                "path": "/debtors",
                "method": "GET",
                "description": "Obtiene la lista de deudores"
            },
            {
                "path": "/debtors",
                "method": "POST",
                "description": "Crea un nuevo deudor"
            },
            {
                "path": "/debtors/<int:debtor_id>",
                "method": "PUT",
                "description": "Actualiza un deudor"
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
            },
            {
                "path": "/scores/delete-all",
                "method": "DELETE",
                "description": "Elimina todas las puntuaciones"
            },
            {
                "path": "/roles",
                "method": "GET",
                "description": "Obtiene la lista de roles"
            },
            {
                "path": "/roles",
                "method": "POST",
                "description": "Crea un nuevo rol"
            },
            {
                "path": "/roles/<int:role_id>",
                "method": "PUT",
                "description": "Actualiza un rol existente"
            },
            {
                "path": "/roles/<int:role_id>",
                "method": "DELETE",
                "description": "Elimina un rol existente"
            },
            {
                "path": "/email/send",
                "method": "POST",
                "description": "Envía un email"
            },
            {
                "path": "/logs",
                "method": "GET",
                "description": "Obtiene los logs del sistema"
            }
        ]
    }
    return jsonify(endpoints), 200

# Rutas de la API
app.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
app.add_url_rule('/docs', 'docs', DocsController.get_docs, methods=['GET'])

# Rutas de usuarios y permisos
app.add_url_rule('/users', 'get_users', UserController.get_users, methods=['GET'])
app.add_url_rule('/users', 'create_user', create_user, methods=['POST'])
app.add_url_rule('/users/permissions', 'get_user_permissions', get_user_permissions, methods=['GET'])
app.add_url_rule('/users/<int:user_id>/toggle-status', 'toggle_user_status', UserController.toggle_user_status, methods=['POST'])
app.add_url_rule('/users/<int:user_id>', 'update_user', update_user, methods=['PUT'])
app.add_url_rule('/users/<int:user_id>/reset-password', 'reset_password', reset_password, methods=['POST'])
app.add_url_rule('/users/change-password', 'change_password', change_password, methods=['POST'])

# Rutas de gastos
app.add_url_rule('/expenses', view_func=ExpenseController.create_expense, methods=['POST'])
app.add_url_rule('/expenses', view_func=ExpenseController.get_expenses, methods=['GET'])
app.add_url_rule('/expenses/<int:expense_id>', view_func=ExpenseController.delete_expense, methods=['DELETE'])
app.add_url_rule('/expenses/<int:expense_id>/invoice', view_func=ExpenseController.get_invoice, methods=['GET'])

# Rutas de deudas
app.add_url_rule('/debts', 'get_debts', DebtController.get_debts, methods=['GET'])
app.add_url_rule('/debts', 'create_debt', DebtController.create_debt, methods=['POST'])
app.add_url_rule('/debts/<int:debt_id>', 'update_debt', DebtController.update_debt, methods=['PATCH'])
app.add_url_rule('/debts/<int:debt_id>', 'delete_debt', DebtController.delete_debt, methods=['DELETE'])

# Rutas de puntuaciones
app.add_url_rule('/scores', 'save_score', ScoreController.save_score, methods=['POST'])
app.add_url_rule('/scores/top', 'get_top_scores', ScoreController.get_top_scores, methods=['GET'])
app.add_url_rule('/scores/delete-all', 'delete_all_scores', ScoreController.delete_all_scores, methods=['DELETE'])

# Rutas de roles
app.add_url_rule('/roles', 'get_roles', RoleController.get_roles, methods=['GET'])
app.add_url_rule('/roles', 'create_role', RoleController.create_role, methods=['POST'])
app.add_url_rule('/roles/<int:role_id>', 'update_role', RoleController.update_role, methods=['PUT'])
app.add_url_rule('/roles/<int:role_id>', 'delete_role', RoleController.delete_role, methods=['DELETE'])

# Rutas de correo
app.add_url_rule('/email/send', 'send_email', EmailController.send_email, methods=['POST'])

# Rutas para deudores
app.add_url_rule('/debtors', view_func=DebtorController.get_debtors, methods=['GET'])
app.add_url_rule('/debtors', view_func=DebtorController.create_debtor, methods=['POST'])
app.add_url_rule('/debtors/<int:debtor_id>', view_func=DebtorController.update_debtor, methods=['PUT'])

# Rutas protegidas
app.add_url_rule('/inicio', 'inicio', BasicController.inicio, methods=['GET'])
app.add_url_rule('/fin', 'fin', BasicController.fin, methods=['GET'])

# Rutas para logs
app.add_url_rule('/logs', view_func=LogController.get_logs, methods=['GET'])

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