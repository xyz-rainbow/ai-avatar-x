import webview
import threading
import time
import sys
from io import StringIO
from backend.app import app

# Capture stdout/stderr (simplified for now)
class StreamCapture(StringIO):
    def __init__(self):
        super().__init__()
        self.terminal_output = []

    def write(self, s):
        super().write(s)
        self.terminal_output.append(s)

    def get_output(self):
        return "".join(self.terminal_output)

    def get_last_lines(self, n=100):
        return "".join(self.terminal_output[-n:])

# Create a global capture object
sys_stdout = sys.stdout
sys_stderr = sys.stderr
captured_output = StreamCapture()
sys.stdout = captured_output
sys.stderr = captured_output

# Function to run the Flask app in a background thread
def run_flask():
    app.run(host='127.0.0.1', port=5000)

# Class to expose Python functions to JavaScript (simplified for now)
class Api:
    def open_control_window(self):
        # Check if a control window already exists
        control_exists = False
        for w in webview.windows:
            if w.title == 'Avatar Control':
                control_exists = True
                w.restore()
                break
        
        if not control_exists:
            webview.create_window(
                'Avatar Control',
                'http://127.0.0.1:5000/control',
                width=400,
                height=600,
                resizable=True,
                frameless=False,
                on_top=False,
                js_api=api
            )

    def open_settings_window(self):
        print("Settings window not implemented in this basic version.")

    def minimize_avatar_window(self):
        if webview.windows:
            webview.windows[0].minimize() # Assuming avatar window is the first
        
    def close_avatar_window(self):
        if webview.windows:
            webview.windows[0].destroy() # Assuming avatar window is the first

    def quit_app(self):
        print("--- Application requested to quit ---")
        sys.exit(0) # Terminate the Python process
api = Api() # Instantiate the API class

if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give the server a moment to start up before creating the window
    time.sleep(1)

    # Pass the captured output object to the Flask app
    app.config['CAPTURED_OUTPUT'] = captured_output

    # Create the main avatar window
    avatar_window = webview.create_window(
        'Gemini Avatar',
        'http://127.0.0.1:5000',
        width=400,
        height=550,
        resizable=False,
        frameless=True,
        on_top=True,
        js_api=api # Expose the API object to JavaScript
    )

    # Start the webview event loop
    webview.start()

    # Restore stdout/stderr when webview closes
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr
