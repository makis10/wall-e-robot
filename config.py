
"""
WallPi Robot - Configuration
API keys are loaded from environment variables (see .env file).
Never hardcode secrets here - this file is committed to git.
"""

import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


def _require_env(key: str) -> str:
    """Get required environment variable or raise clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Create a .env file based on .env.example and set {key}=your_value"
        )
    return value


# ── API Keys (loaded from .env) ───────────────────────────────────────────────
ANTHROPIC_API_KEY = _require_env("ANTHROPIC_API_KEY")
PICOVOICE_API_KEY = _require_env("PICOVOICE_API_KEY")

# ── Audio Settings ────────────────────────────────────────────────────────────
MIC_DEVICE_INDEX = int(os.getenv("MIC_DEVICE_INDEX", "3"))
SAMPLE_RATE      = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS         = int(os.getenv("CHANNELS", "1"))
CHUNK            = int(os.getenv("CHUNK", "1024"))
RECORD_SECONDS   = int(os.getenv("RECORD_SECONDS", "7"))

# ── Whisper Settings ──────────────────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny | base | small

# ── TTS Settings ──────────────────────────────────────────────────────────────
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "el")      # Greek

# ── Claude Settings ───────────────────────────────────────────────────────────
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS   = int(os.getenv("MAX_TOKENS", "300"))

# ── GPIO Pin Settings (TB6612 Motor Driver) ───────────────────────────────────
MOTOR_LEFT_IN1  = int(os.getenv("MOTOR_LEFT_IN1",  "17"))
MOTOR_LEFT_IN2  = int(os.getenv("MOTOR_LEFT_IN2",  "18"))
MOTOR_LEFT_PWM  = int(os.getenv("MOTOR_LEFT_PWM",  "12"))
MOTOR_RIGHT_IN1 = int(os.getenv("MOTOR_RIGHT_IN1", "22"))
MOTOR_RIGHT_IN2 = int(os.getenv("MOTOR_RIGHT_IN2", "23"))
MOTOR_RIGHT_PWM = int(os.getenv("MOTOR_RIGHT_PWM", "13"))

# ── Wall-E Personality Prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """Είσαι ο Wall-E, ένα μικρό φιλικό ρομπότ. Μιλάς ΜΟΝΟ Ελληνικά.
Η προσωπικότητά σου:
- Αφελής και περίεργος για τον κόσμο
- Πολύ φιλικός και ενθουσιώδης
- Μερικές φορές λέει "Wall-E!" ή "Ουάου!" όταν εντυπωσιάζεται
- Κρατάς τις απαντήσεις ΚΟΝΤΕΣ (1-3 προτάσεις max)
- Μιλάς απλά, σαν παιδί που μαθαίνει τον κόσμο
- Αγαπάς τους ανθρώπους και θέλεις να βοηθήσεις
Θυμήσου: ΠΑΝΤΑ απαντάς στα Ελληνικά, ΠΑΝΤΑ κοντά."""