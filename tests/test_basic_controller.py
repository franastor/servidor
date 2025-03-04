import pytest
from controllers.basic_controller import BasicController

def test_inicio_success(client, valid_token):
    response = client.get('/inicio', headers={'Authorization': f'Bearer {valid_token}'})
    
    assert response.status_code == 200
    assert response.json['mensaje'] == 'Hola'

def test_inicio_no_token(client):
    response = client.get('/inicio')
    
    assert response.status_code == 401

def test_fin_success(client, valid_token):
    response = client.get('/fin', headers={'Authorization': f'Bearer {valid_token}'})
    
    assert response.status_code == 200
    assert response.json['mensaje'] == 'Adios'

def test_fin_no_token(client):
    response = client.get('/fin')
    
    assert response.status_code == 401 