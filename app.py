from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from controllers.basic_controller import BasicController
from controllers.auth_controller import AuthController
from controllers.docs_controller import DocsController

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

if __name__ == '__main__':
    app.run(debug=True, port=5001) 