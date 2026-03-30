import subprocess
import os
import sys

def run():
    print("🌹 XYZ Rainbow Technology - Makima Avatar Installer")
    
    try:
        print("--- Creating Virtual Environment ---")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        
        # Path to the venv python/pip
        if os.name == 'nt': # Windows
            pip_path = os.path.join("venv", "Scripts", "pip")
        else: # Linux/Mac
            pip_path = os.path.join("venv", "bin", "pip")
            
        print("--- Installing Dependencies ---")
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        
        print("\n✅ Installation successful!")
        print("🚀 Run 'python run.py' (inside venv) to start.")
        
    except Exception as e:
        print(f"\n❌ Error during installation: {e}")

if __name__ == "__main__":
    run()

