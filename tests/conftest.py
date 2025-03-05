import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import os
from dotenv import load_dotenv
from controllers.auth_controller import AuthController
from controllers.basic_controller import BasicController
from controllers.docs_controller import DocsController
from controllers.score_controller import ScoreController
from datetime import timedelta

@pytest.fixture
def app():
    load_dotenv()
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test_secret_key')
    app.config['TESTING'] = True
    jwt = JWTManager(app)

    # Registrar rutas
    app.add_url_rule('/login', 'login', AuthController.login, methods=['POST'])
    app.add_url_rule('/inicio', 'inicio', BasicController.inicio, methods=['GET'])
    app.add_url_rule('/fin', 'fin', BasicController.fin, methods=['GET'])
    app.add_url_rule('/docs', 'docs', DocsController.get_docs, methods=['GET'])
    app.add_url_rule('/scores', 'save_score', ScoreController.save_score, methods=['POST'])
    app.add_url_rule('/scores/top', 'get_top_scores', ScoreController.get_top_scores, methods=['GET'])

    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db_connection(mocker):
    mock_connection = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    return mock_connection, mock_cursor

@pytest.fixture
def valid_token(app):
    with app.app_context():
        return create_access_token(
            identity='usuario_prueba',
            expires_delta=timedelta(hours=1)
        ) 