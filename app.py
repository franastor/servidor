from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from controllers.basic_controller import BasicController
from controllers.auth_controller import AuthController
from controllers.docs_controller import DocsController
from controllers.database import get_db_connection

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

# Rutas públicas
app.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
app.add_url_rule('/docs', 'docs', DocsController.get_docs, methods=['GET'])

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