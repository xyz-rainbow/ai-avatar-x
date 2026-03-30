"""
#xyz-rainbow #xyz-rainbowtechnology #rainbowtechnology.xyz #rainbow.xyz #rainbow@rainbowtechnology.xyz
#i-love-you #You're not supposed to see this!

  __  ____   _______
  \ \/ /\ \ / /__  /
   \  /  \ V /  / / 
   /  \   | |  / /_ 
  /_/\_\  |_/ /____|

Este es el punto de entrada principal para la aplicación Gemini Avatar.
Gestiona el servidor Flask y la interfaz de usuario nativa con pywebview.
"""

import webview
import threading
import time
import sys
import os
from io import StringIO
from backend.app import app

# Captura de la salida estándar y de errores para mostrar en los logs de la interfaz
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

# Configuración global para la captura de logs
sys_stdout = sys.stdout
sys_stderr = sys.stderr
captured_output = StreamCapture()
sys.stdout = captured_output
sys.stderr = captured_output

def run_flask():
    """Ejecuta el servidor Flask en un hilo secundario."""
    app.run(host='127.0.0.1', port=5000)

class Api:
    """Clase para exponer funciones de Python a JavaScript a través de pywebview."""
    
    def open_control_window(self):
        """Abre o restaura la ventana del panel de control."""
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
                js_api=self
            )

    def open_settings_window(self):
        """Abre la ventana de configuración."""
        # Se implementará en futuras versiones
        print("[INFO] Ventana de configuración solicitada.")

    def open_inspector(self):
        """Abre las herramientas de desarrollador."""
        if webview.windows:
            webview.windows[0].show_devtools()

    def minimize_avatar_window(self):
        """Minimiza la ventana principal del avatar."""
        if webview.windows:
            webview.windows[0].minimize()
        
    def close_avatar_window(self):
        """Cierra la ventana principal y finaliza la aplicación."""
        if webview.windows:
            webview.windows[0].destroy()

    def quit_app(self):
        """Finaliza el proceso de la aplicación por completo."""
        print("--- La aplicación ha solicitado cerrarse ---")
        os._exit(0) # Salida forzada para cerrar todos los hilos

api = Api()

if __name__ == '__main__':
    # Iniciar Flask en un hilo de fondo
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Esperar un momento para que el servidor esté listo
    time.sleep(1)

    # Pasar el objeto de captura de logs a la configuración de Flask
    app.config['CAPTURED_OUTPUT'] = captured_output

    # Crear la ventana principal con transparencia real
    avatar_window = webview.create_window(
        'Gemini Avatar',
        'http://127.0.0.1:5000',
        width=400,
        height=550,
        resizable=False,
        frameless=True,
        on_top=True,
        transparent=True, # Activar transparencia de ventana
        js_api=api
    )

    # Iniciar el bucle de eventos de webview
    webview.start()

    # Restaurar stdout/stderr al cerrar
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr
