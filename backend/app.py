"""
#xyz-rainbow #xyz-rainbowtechnology #rainbowtechnology.xyz #rainbow.xyz #rainbow@rainbowtechnology.xyz
#i-love-you #You're not supposed to see this!

 ____      _    ___ _   _ ____   _____        __ 
|  _ \    / \  |_ _| \ | | __ ) / _ \ \      / / 
| |_) |  / _ \  | ||  \| |  _ \| | | \ \ /\ / /  
|  _ <  / ___ \ | || |\  | |_) | |_| |\ V  V /   
|_| \_\/_/   \_\___|_| \_|____/ \___/  \_\/\_/    

Backend de la aplicación Gemini Avatar con soporte para pensamientos y Ollama.
"""

import os
import time
import threading
import random
import json
import requests
from flask import Flask, jsonify, send_from_directory, request

# --- Configuración de Rutas ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(backend_dir, '..', 'frontend')
CONFIG_FILE = os.path.join(backend_dir, 'config.json')
I18N_FILE = os.path.join(backend_dir, 'i18n.json')

# --- Carga de Configuración ---
config = {}
def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "ollama_enabled": True,
                "ollama_url": "http://localhost:11434/api/generate",
                "ollama_model": "llama3",
                "thought_mode": "short",
                "system_prompt": "Eres Makima. Responde en JSON con keys 'thought', 'expression' y 'subtitle'."
            }
    except Exception as e:
        print(f"[ERROR CONFIG] {e}")

load_config()

# --- Configuración de la Aplicación ---
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# --- Gestión del Estado ---
global_state = {
    "expression": "neutral",
    "subtitle": "",
    "thought": ""
}
last_manual_command_time = time.time()

allowed_expressions = [
    "neutral", "orgullosa", "angry", "annoyed", "idle1", "idle2", "idle3", "idle4",
    "nervous", "sad", "sleepy", "happy", "thinking", "talking", "wink", "idea",
    "idea2", "curious", "excited"
]
idle_cycle_expressions = ["idle1", "idle2", "idle3", "idle4"]

# --- API Endpoints ---

@app.route('/')
def index(): return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/state')
def get_state(): return jsonify(global_state)

@app.route('/api/config', methods=['GET'])
def get_config(): return jsonify(config)

@app.route('/api/i18n')
def get_i18n_full():
    return jsonify(translations)

@app.route('/api/config', methods=['POST'])
def save_config():
    new_cfg = request.get_json()
    config.update(new_cfg)
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        load_config()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        # Extraer base URL de Ollama para listar tags
        url = config.get('ollama_url', 'http://localhost:11434/api/generate')
        base_url = url.split('/api/')[0]
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            return jsonify([m['name'] for m in resp.json().get('models', [])])
    except: pass
    return jsonify(["llama3", "qwen3.5:0.8b"])

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    data = request.get_json()
    message = data.get('message', '').lower()
    
    if config.get("ollama_enabled", True):
        try:
            url = config.get("ollama_url", "http://localhost:11434/api/generate")
            model = config.get("ollama_model", "llama3")
            
            # Construcción del Prompt con instrucciones de formato
            prompt = f"{config.get('system_prompt', '')}\n\nUsuario: {message}\nAsistente (JSON):"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "keep_alive": config.get("ollama_keep_alive", "5m")
            }
            
            print(f"[OLLAMA] Petición a {url} con modelo {model}...")
            resp = requests.post(url, json=payload, timeout=60)
            
            if resp.status_code == 200:
                data = resp.json()
                raw_response = data.get("response", "").strip()
                if not raw_response: raw_response = data.get("thinking", "").strip()
                
                print(f"[OLLAMA RESPONSE] {raw_response}")
                
                try:
                    parsed = json.loads(raw_response)
                    msg_list = parsed if isinstance(parsed, list) else [parsed]
                    
                    final_sequence = []
                    for item in msg_list[:5]:
                        subtitle = item.get("subtitle", "").strip()
                        # Only add if there is actual speech
                        if subtitle:
                            exp = item.get("expression", "neutral")
                            if exp not in allowed_expressions: exp = "neutral"
                            
                            final_sequence.append({
                                "expression": exp,
                                "subtitle": subtitle,
                                "thought": item.get("thought", "") if config.get("thought_mode") != "none" else ""
                            })
                    
                    # Safety fallback if list ended up empty but we had a thought
                    if not final_sequence and msg_list:
                        first = msg_list[0]
                        final_sequence.append({
                            "expression": first.get("expression", "neutral"),
                            "subtitle": "...", 
                            "thought": first.get("thought", "...")
                        })

                    return jsonify(final_sequence)
                except Exception as e:
                    print(f"[PARSE ERROR] {e}")
                    return jsonify([{"expression": "talking", "subtitle": raw_response, "thought": ""}])
            else:
                print(f"[OLLAMA ERROR] HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            error_msg = f"Error: {type(e).__name__} - {str(e)}"
            print(f"[OLLAMA EXCEPTION] {error_msg}")
            return jsonify([{"expression": "sad", "subtitle": "Fallo de conexión.", "thought": error_msg}])

    return jsonify([{"expression": "sad", "subtitle": "Ollama desactivado.", "thought": "Actívalo en config.json"}])

# --- Lógica Idle ---
def manage_idle_state():
    global last_manual_command_time
    while True:
        time.sleep(1)
        if time.time() - last_manual_command_time < config.get("inactivity_delay", 7):
            continue
        if random.random() < 0.05:
            global_state['expression'] = random.choice(idle_cycle_expressions)
            global_state['subtitle'] = ""
            global_state['thought'] = ""

threading.Thread(target=manage_idle_state, daemon=True).start()

if __name__ == "__main__":
    app.run(port=5000)
