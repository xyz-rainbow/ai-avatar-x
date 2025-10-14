import os
import time
import threading
import random
import json
from flask import Flask, jsonify, send_from_directory, request

# --- Path Configuration ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(backend_dir, '..', 'frontend')
COMMAND_FILE = os.path.join(backend_dir, 'command.txt')

# --- App Configuration ---
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# --- State Management ---
global_state = {
    "expression": "neutral",
    "subtitle": ""
}
last_manual_command_time = time.time()

# --- Avatar Personality Configuration ---

# All available expression video files
allowed_expressions = [
    "neutral", "orgullosa", "angry", "annoyed", "idle1", "idle2", "idle3", "idle4",
    "nervous", "sad", "sleepy", "happy", "thinking", "talking", "wink", "idea",
    "idea2", "curious", "excited"
]

# Specific idle states to cycle through
idle_cycle_expressions = ["idle1", "idle2", "idle3", "idle4"]

# Generic subtitles for random thoughts
sample_subtitles = [
    "Hmm...", "¿Qué debería hacer ahora?", "Tengo un poco de hambre.",
    "Esto es interesante.", "...", "Zzz...", "¡Ah!",
    "Me pregunto qué estará pensando.", "Un día productivo.", "¿Y si...?",
    "Necesito un café."
]

# Subtitles that trigger a specific expression
emotional_events = [
    ("¿Estás ahí?", "curious"),
    ("¡Deja de ignorarme!", "angry"),
    ("¡Tengo una idea!", "idea"),
    ("Eso es... inesperado.", "nervous"),
    ("¡Me encanta esto!", "excited")
]

# --- Idle Mode Logic ---
def manage_idle_state():
    global last_manual_command_time
    
    inactivity_delay = 7  # Start idle mode after 7 seconds
    long_idle_interval = 40 # Major change every 40 seconds

    last_short_idle_change = time.time()
    last_long_idle_change = time.time()
    last_subtitle_change = time.time()

    next_short_idle_interval = random.randint(4, 10)
    next_subtitle_interval = random.randint(5, 18)

    while True:
        time.sleep(1)

        if time.time() - last_manual_command_time < inactivity_delay:
            continue

        # --- Subtitle & Emotional Event Logic ---
        if time.time() - last_subtitle_change > next_subtitle_interval:
            # 25% chance of an emotional event, 75% for a normal subtitle
            if random.random() < 0.25 and emotional_events:
                subtitle, expression = random.choice(emotional_events)
                global_state['subtitle'] = subtitle
                global_state['expression'] = expression
                print(f"[IDLE-EVENT] Triggered event: {subtitle} -> {expression}")
                # This is a major event, so reset the other timers
                last_long_idle_change = time.time()
                last_short_idle_change = time.time()
            else:
                # 50% chance of a generic subtitle, 50% chance of clearing it
                if random.random() < 0.5 and sample_subtitles:
                    global_state['subtitle'] = random.choice(sample_subtitles)
                else:
                    global_state['subtitle'] = ""
            
            last_subtitle_change = time.time()
            next_subtitle_interval = random.randint(5, 18)

        # --- Expression Change Logic ---
        if time.time() - last_long_idle_change > long_idle_interval:
            new_expression = random.choice(allowed_expressions)
            global_state['expression'] = new_expression
            print(f"[IDLE-LONG] New expression: {new_expression}")
            last_long_idle_change = time.time()
            last_short_idle_change = time.time()

        elif time.time() - last_short_idle_change > next_short_idle_interval:
            current_expression = global_state['expression']
            # Filter out the current expression to avoid repeats
            available_idles = [e for e in idle_cycle_expressions if e != current_expression]
            if available_idles:
                new_expression = random.choice(available_idles)
                global_state['expression'] = new_expression
                global_state['subtitle'] = "" # Clear subtitle on minor idle change
                print(f"[IDLE-SHORT] New expression: {new_expression}")
            
            last_short_idle_change = time.time()
            next_short_idle_interval = random.randint(4, 10)

# --- Command Processing Logic ---
def watch_command_file():
    global last_manual_command_time
    print("--- Command file watcher started ---")
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r') as f:
                    command_data = f.read().strip()
                os.remove(COMMAND_FILE)

                command, subtitle = None, ""
                try:
                    cmd_obj = json.loads(command_data)
                    command = cmd_obj.get('expression')
                    subtitle = cmd_obj.get('subtitle', "")
                except json.JSONDecodeError:
                    command = command_data

                if command in allowed_expressions:
                    global_state['expression'] = command
                    global_state['subtitle'] = subtitle
                    last_manual_command_time = time.time()
                    print(f"[MANUAL] State updated: {global_state}")
                else:
                    print(f"Warning: Received invalid command '{command}' from file.")
            
        except Exception as e:
            print(f"Error in command watcher: {e}")
        time.sleep(0.5)

# --- API & Frontend Routes ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(global_state)

@app.route('/control')
def control_panel():
    return send_from_directory(app.static_folder, 'control.html')

@app.route('/settings')
def settings_panel():
    return send_from_directory(app.static_folder, 'settings.html')

@app.route('/api/logs')
def get_logs():
    captured_output = app.config.get('CAPTURED_OUTPUT')
    if captured_output:
        return jsonify(logs=captured_output.get_output())
    return jsonify(logs="Log capture not initialized."), 500

@app.route('/api/terminal_input', methods=['POST'])
def terminal_input_handler():
    data = request.get_json()
    text_input = data.get('text', '').strip()
    if not text_input: return jsonify({"success": False, "error": "No text provided"}), 400

    expression_to_set, subtitle_to_set = global_state['expression'], ""
    if text_input in allowed_expressions:
        expression_to_set = text_input
    else:
        subtitle_to_set = text_input

    try:
        with open(COMMAND_FILE, 'w') as f:
            json.dump({'expression': expression_to_set, 'subtitle': subtitle_to_set}, f)
        return jsonify({"success": True, "message": f"Command '{text_input}' processed."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    data = request.get_json()
    message = data.get('message', '').lower()

    # Simple rule-based responses
    if 'hello' in message or 'hi' in message:
        response_sequence = [
            {"expression": "happy", "subtitle": "Hello there!"},
            {"expression": "curious", "subtitle": "How can I help you today?"}
        ]
    elif 'how are you' in message:
        response_sequence = [
            {"expression": "happy", "subtitle": "I'm doing great, thanks for asking!"},
            {"expression": "orgullosa", "subtitle": "Ready to tackle any task."}
        ]
    elif 'idea' in message:
        response_sequence = [
            {"expression": "idea", "subtitle": "You have an idea?"},
            {"expression": "excited", "subtitle": "I'm excited to hear it!"}
        ]
    else:
        response_sequence = [
            {"expression": "thinking", "subtitle": "I'm not sure how to respond to that."},
            {"expression": "sad", "subtitle": "I'm still learning."}
        ]

    return jsonify(response_sequence)

@app.route('/api/update_from_gui', methods=['POST'])
def update_from_gui():
    data = request.get_json()
    expression, subtitle = data.get('expression'), data.get('subtitle', "")
    if expression and expression in allowed_expressions:
        try:
            with open(COMMAND_FILE, 'w') as f:
                json.dump({'expression': expression, 'subtitle': subtitle}, f)
            return jsonify({"success": True, "message": f"Command '{expression}' sent."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "Invalid expression"}), 400

# --- Main Execution ---
command_watcher_thread = threading.Thread(target=watch_command_file, daemon=True)
command_watcher_thread.start()

idle_manager_thread = threading.Thread(target=manage_idle_state, daemon=True)
idle_manager_thread.start()
