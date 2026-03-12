# WallPi 🤖

A Wall-E inspired robot powered by Claude AI, running on Raspberry Pi 4.

## Features

- 🎤 Wake command detection ("Hey Walle") via Picovoice Porcupine
- 🔤 Speech-to-text via OpenAI Whisper (runs locally)
- 🧠 AI responses via Anthropic Claude (Wall-E personality, Greek language)
- 🔊 Text-to-speech via gTTS (Greek)
- 🚗 Motor control via TB6612 driver
- 💃 Reacts to greetings with a happy dance

## Hardware

- Raspberry Pi 4 Model B (4GB)
- USB Microphone
- PAM8403 Amplifier + 2W 8Ohm Speaker
- 2WD Robot Chassis with DC motors
- TB6612 Dual Motor Driver
- OLED 128x64 SSD1306 (optional, for eyes)

## Project Structure

```
wall-e-robot/
├── main.py              # Entry point
├── config.py            # Configuration & API keys
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── src/
│   ├── robot.py         # Main orchestrator
│   ├── wake_command.py     # Porcupine wake word detection
│   ├── speech_to_text.py # Whisper STT
│   ├── claude_brain.py  # Claude AI integration
│   ├── text_to_speech.py # gTTS speech output
│   └── motors.py        # TB6612 motor control
└── scripts/
    └── install.sh       # Setup script for Raspberry Pi
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/makis10/wall-e-robot.git
cd wall-e-robot
```

### 2. API Keys

You need:
- **Anthropic API key**: https://console.anthropic.com/
- **Picovoice API key**: https://console.picovoice.ai/

Edit `config.py` and fill in your keys.

### 3. Install dependencies (on Raspberry Pi)

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev python3-pyaudio ffmpeg espeak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run

```bash
source venv/bin/activate
python main.py
```

## Wake Command

By default, uses "Hey Google" as the wake Command (built-in Porcupine keyword).

To use a custom "Hey Walli" wake command:
1. Go to https://console.picovoice.ai/
2. Create a custom wake command
3. Download the `.ppn` file for Raspberry Pi
4. Place it in the project root as `hey-walli.ppn`

## Motor Commands (voice)

Say the wake command, then:
- "πήγαινε μπροστά" → moves forward
- "πήγαινε πίσω" → moves backward
- "αριστερά" → turns left
- "δεξιά" → turns right
- "σταμάτα" → stops
- "χόρεψε" → happy dance

## Development Workflow

```bash
# On MacBook: write code, then push
git add .
git commit -m "feat: description"
git push

# On Raspberry Pi: pull and run
git pull && source venv/bin/activate && python main.py
```