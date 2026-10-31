import pytest
import json
import os
import sys

# Add root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import app, load_config, get_i18n_data
import backend.app as backend_app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_load_config_default(mocker):
    # Test loading config when file does not exist
    mocker.patch('os.path.exists', return_value=False)
    load_config()
    assert backend_app.config["ollama_enabled"] == True
    assert backend_app.config["ollama_model"] == "llama3"

def test_load_config_existing(mocker, tmp_path):
    # Test loading config when file exists
    test_config = {"ollama_enabled": False, "ollama_model": "test_model"}
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(test_config, f)

    mocker.patch('backend.app.CONFIG_FILE', str(config_file))
    mocker.patch('os.path.exists', return_value=True)
    load_config()

    assert backend_app.config["ollama_enabled"] == False
    assert backend_app.config["ollama_model"] == "test_model"

def test_get_i18n_data(mocker, tmp_path):
    # Create dummy i18n file
    i18n_data = {
        "en": {"ui": {"test": "English"}},
        "es": {"ui": {"test": "Spanish"}}
    }
    i18n_file = tmp_path / "i18n.json"
    with open(i18n_file, "w") as f:
        json.dump(i18n_data, f)

    mocker.patch('backend.app.I18N_FILE', str(i18n_file))
    mocker.patch('os.path.exists', return_value=True)

    # Test default English
    backend_app.config["language"] = "en"
    data = get_i18n_data()
    assert data["ui"]["test"] == "English"

    # Test Spanish
    backend_app.config["language"] = "es"
    data = get_i18n_data()
    assert data["ui"]["test"] == "Spanish"

    # Test fallback to en if language missing
    backend_app.config["language"] = "fr"
    data = get_i18n_data()
    assert data["ui"]["test"] == "English"

def test_get_i18n_full_endpoint(client, mocker, tmp_path):
    # Create dummy i18n file
    i18n_data = {
        "en": {"ui": {"test": "English"}},
        "es": {"ui": {"test": "Spanish"}}
    }
    i18n_file = tmp_path / "i18n.json"
    with open(i18n_file, "w") as f:
        json.dump(i18n_data, f)

    mocker.patch('backend.app.I18N_FILE', str(i18n_file))
    mocker.patch('os.path.exists', return_value=True)

    response = client.get('/api/i18n')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "en" in data
    assert "es" in data
    assert data["en"]["ui"]["test"] == "English"

def test_get_models_success(client, requests_mock):
    # Test successful /api/models request
    mock_url = backend_app.config.get('ollama_url', 'http://localhost:11434/api/generate')
    base_url = mock_url.split('/api/')[0]

    mock_response = {
        "models": [
            {"name": "llama3:latest"},
            {"name": "qwen3.5:0.8b"}
        ]
    }
    requests_mock.get(f"{base_url}/api/tags", json=mock_response, status_code=200)

    response = client.get('/api/models')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "llama3:latest" in data
    assert "qwen3.5:0.8b" in data

def test_get_models_fail(client, requests_mock):
    # Test failing /api/models request
    mock_url = backend_app.config.get('ollama_url', 'http://localhost:11434/api/generate')
    base_url = mock_url.split('/api/')[0]

    requests_mock.get(f"{base_url}/api/tags", status_code=500)

    response = client.get('/api/models')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "llama3" in data
    assert "qwen3.5:0.8b" in data

def test_chat_success(client, requests_mock):
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    mock_ollama_response = {
        "response": json.dumps([
            {"expression": "happy", "subtitle": "Hello there!", "thought": "I should greet them."}
        ])
    }
    requests_mock.post(mock_url, json=mock_ollama_response, status_code=200)

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "happy"
    assert data[0]["subtitle"] == "Hello there!"
    assert data[0]["thought"] == "I should greet them."

def test_chat_fallback(client, requests_mock, mocker, tmp_path):
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    # Empty sequence response will trigger fallback
    mock_ollama_response = {
        "response": json.dumps([])
    }
    requests_mock.post(mock_url, json=mock_ollama_response, status_code=200)

    i18n_data = {
        "en": {"ui": {"fallback_reply": "Fallback text"}}
    }
    i18n_file = tmp_path / "i18n.json"
    with open(i18n_file, "w") as f:
        json.dump(i18n_data, f)

    mocker.patch('backend.app.I18N_FILE', str(i18n_file))
    mocker.patch('os.path.exists', return_value=True)
    backend_app.config["language"] = "en"

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "curious"
    assert data[0]["subtitle"] == "Fallback text"

def test_chat_error(client, requests_mock):
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    requests_mock.post(mock_url, status_code=500, text="Internal Server Error")

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "sad"
    assert data[0]["subtitle"] == "Error del servidor."


def test_chat_invalid_expression(client, requests_mock):
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    mock_ollama_response = {
        "response": json.dumps([
            {"expression": "non_existent_expression", "subtitle": "Hello there!", "thought": "I should greet them."}
        ])
    }
    requests_mock.post(mock_url, json=mock_ollama_response, status_code=200)

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    # Invalid expression should fallback to neutral
    assert data[0]["expression"] == "neutral"
    assert data[0]["subtitle"] == "Hello there!"


def test_chat_timeout(client, requests_mock):
    import requests
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    requests_mock.post(mock_url, exc=requests.exceptions.Timeout)

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "sad"
    assert data[0]["subtitle"] == "Tiempo de espera agotado."


def test_chat_connection_error(client, requests_mock):
    import requests
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    requests_mock.post(mock_url, exc=requests.exceptions.ConnectionError)

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "sad"
    assert data[0]["subtitle"] == "Error de conexión con Ollama."


def test_chat_json_decode_error(client, requests_mock):
    mock_url = "http://localhost:11434/api/generate"
    backend_app.config["ollama_enabled"] = True
    backend_app.config["ollama_url"] = mock_url

    mock_ollama_response = {
        "response": "This is not valid json, {just text"
    }
    requests_mock.post(mock_url, json=mock_ollama_response, status_code=200)

    response = client.post('/api/chat', json={"message": "hi"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["expression"] == "talking"
    assert data[0]["subtitle"] == "This is not valid json, {just text"
