#!/bin/bash
# WallPi Installation Script for Raspberry Pi
# Run once after cloning the repo

set -e

echo "🤖 Installing WallPi dependencies..."

# System packages
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    espeak \
    git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Python packages
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.py and add your API keys"
echo "2. Run: source venv/bin/activate && python main.py"
