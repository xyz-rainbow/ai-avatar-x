#!/bin/bash
# XYZ Rainbow Technology - Makima Avatar Installer
echo "🌹 Installing Gemini Avatar (Makima)..."

if ! command -v python3 &> /dev/null
then
    echo "❌ Error: Python 3 is not installed."
    exit
fi

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Installation complete!"
echo "🚀 To start, run: ./venv/bin/python run.py or use the alias if configured."
