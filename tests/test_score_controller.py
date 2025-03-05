import pytest
from unittest.mock import patch, MagicMock
from controllers.score_controller import ScoreController
import os

@pytest.fixture
def mock_db_connection():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    return mock_connection, mock_cursor

@pytest.fixture
def valid_score_data():
    return {
        "name": "Test Player",
        "score": 100,
        "timestamp": 1709654321,
        "session_id": "test123",
        "game_duration": 300,
        "interaction_count": 50,
        "game_version": "1.0.0"
    }

def test_save_score_success(client, mock_db_connection, valid_score_data, master_token):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.lastrowid = 1
    
    with patch('controllers.score_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/scores',
            headers={'X-Master-Token': master_token},
            json=valid_score_data
        )
        
        assert response.status_code == 201
        assert response.json['mensaje'] == "Puntuación guardada exitosamente"
        assert response.json['id'] == 1
        mock_connection.commit.assert_called_once()

def test_save_score_missing_token(client, valid_score_data):
    response = client.post('/scores', json=valid_score_data)
    assert response.status_code == 401
    assert 'error' in response.json

def test_save_score_invalid_token(client, valid_score_data):
    response = client.post('/scores',
        headers={'X-Master-Token': 'token_invalido'},
        json=valid_score_data
    )
    assert response.status_code == 401
    assert 'error' in response.json

def test_save_score_missing_fields(client, mock_db_connection, master_token):
    mock_connection, _ = mock_db_connection
    
    with patch('controllers.score_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/scores',
            headers={'X-Master-Token': master_token},
            json={"name": "Test"}
        )
        
        assert response.status_code == 400
        assert 'error' in response.json

def test_save_score_db_error(client, mock_db_connection, valid_score_data, master_token):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Exception("Error de base de datos")
    
    with patch('controllers.score_controller.get_db_connection', return_value=mock_connection):
        response = client.post('/scores',
            headers={'X-Master-Token': master_token},
            json=valid_score_data
        )
        
        assert response.status_code == 500
        assert 'error' in response.json

def test_get_top_scores_success(client, mock_db_connection, master_token):
    mock_connection, mock_cursor = mock_db_connection
    mock_scores = [
        {
            "name": "Player 1",
            "score": 100,
            "timestamp": 1709654321,
            "session_id": "test123",
            "game_duration": 300,
            "interaction_count": 50,
            "game_version": "1.0.0",
            "platform": "Chrome",
            "user_agent": "Mozilla/5.0",
            "created_at": "2024-03-05T12:00:00"
        }
    ]
    mock_cursor.fetchall.return_value = mock_scores
    
    with patch('controllers.score_controller.get_db_connection', return_value=mock_connection):
        response = client.get('/scores/top',
            headers={'X-Master-Token': master_token}
        )
        
        assert response.status_code == 200
        assert response.json['mensaje'] == "Top 10 puntuaciones"
        assert len(response.json['scores']) == 1
        assert response.json['scores'][0]['name'] == "Player 1"

def test_get_top_scores_missing_token(client):
    response = client.get('/scores/top')
    assert response.status_code == 401
    assert 'error' in response.json

def test_get_top_scores_invalid_token(client):
    response = client.get('/scores/top',
        headers={'X-Master-Token': 'token_invalido'}
    )
    assert response.status_code == 401
    assert 'error' in response.json

def test_get_top_scores_db_error(client, mock_db_connection, master_token):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Exception("Error de base de datos")
    
    with patch('controllers.score_controller.get_db_connection', return_value=mock_connection):
        response = client.get('/scores/top',
            headers={'X-Master-Token': master_token}
        )
        
        assert response.status_code == 500
        assert 'error' in response.json 