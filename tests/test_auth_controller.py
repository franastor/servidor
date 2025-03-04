import pytest
from unittest.mock import patch
from controllers.auth_controller import AuthController

def test_login_success(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'usuario': 'usuario_prueba',
        'password': 'password_prueba'
    }
    
    with patch('controllers.auth_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/login', json={
            'usuario': 'usuario_prueba',
            'password': 'password_prueba'
        })
        
        assert response.status_code == 200
        assert 'token' in response.json
        assert response.json['usuario'] == 'usuario_prueba'

def test_login_invalid_credentials(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    with patch('controllers.auth_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/login', json={
            'usuario': 'usuario_incorrecto',
            'password': 'password_incorrecta'
        })
        
        assert response.status_code == 401
        assert 'error' in response.json

def test_login_user_not_exists(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    with patch('controllers.auth_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/login', json={
            'usuario': 'usuario_no_existente',
            'password': 'cualquier_password'
        })
        
        assert response.status_code == 401
        assert 'error' in response.json
        assert response.json['error'] == 'Usuario o contraseña incorrectos'

def test_login_missing_data(client):
    response = client.post('/login', json={})
    
    assert response.status_code == 400
    assert 'error' in response.json

def test_login_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Exception("Error de base de datos")
    
    with patch('controllers.auth_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/login', json={
            'usuario': 'usuario_prueba',
            'password': 'password_prueba'
        })
        
        assert response.status_code == 500
        assert 'error' in response.json 