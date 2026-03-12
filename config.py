# WallPi Robot - Configuration
# Replace the placeholder values with your actual API keys

# Anthropic API Key (Claude)
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"

# Picovoice Porcupine API Key (Wake Word)
PICOVOICE_API_KEY = "xi9Z9SaP+XYQb+DmNdGjDHPlyj0b18EjI3yve+hXmHy07vycOdaw9g=="

# Audio settings
MIC_DEVICE_INDEX = 3        # Card index from `arecord -l`
SAMPLE_RATE = 16000         # Hz - optimal for Whisper
CHANNELS = 1                # Mono microphone
CHUNK = 1024                # Audio buffer size
RECORD_SECONDS = 7          # Max recording duration after wake word

# Whisper settings
WHISPER_MODEL = "base"      # tiny | base | small (base = good balance for Pi 4)

# TTS settings
TTS_LANGUAGE = "el"         # Greek

# Claude settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 300            # Keep responses short for TTS

# GPIO settings (for motors - TB6612)
# Left motor
MOTOR_LEFT_IN1 = 17
MOTOR_LEFT_IN2 = 18
MOTOR_LEFT_PWM = 12

# Right motor
MOTOR_RIGHT_IN1 = 22
MOTOR_RIGHT_IN2 = 23
MOTOR_RIGHT_PWM = 13

# System prompt for Wall-E personality
SYSTEM_PROMPT = """Είσαι ο Wall-E, ένα μικρό φιλικό ρομπότ. Μιλάς ΜΟΝΟ Ελληνικά.
Η προσωπικότητά σου:
- Αφελής και περίεργος για τον κόσμο
- Πολύ φιλικός και ενθουσιώδης
- Μερικές φορές λέει "Wall-E!" ή "Ουάου!" όταν εντυπωσιάζεται
- Κρατάς τις απαντήσεις ΚΟΝΤΕΣ (1-3 προτάσεις max)
- Μιλάς απλά, σαν παιδί που μαθαίνει τον κόσμο
- Αγαπάς τους ανθρώπους και θέλεις να βοηθήσεις
Θυμήσου: ΠΑΝΤΑ απαντάς στα Ελληνικά, ΠΑΝΤΑ κοντά."""