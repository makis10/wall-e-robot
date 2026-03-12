"""
WallPi Robot - Main orchestrator.
Ties together wake word, STT, Claude AI, TTS, and motors.
"""

import logging
import time
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config
from src.wake_command import WakeWordDetectorDetector
from src.speech_to_text import SpeechToText
from src.claude_brain import ClaudeBrain
from src.text_to_speech import TextToSpeech
from src.motors import Motors

logger = logging.getLogger(__name__)

# Keywords that trigger motor movement
MOVE_KEYWORDS = {
    "μπροστά": "forward",
    "εμπρός": "forward",
    "πίσω": "backward",
    "αριστερά": "left",
    "δεξιά": "right",
    "σταμάτα": "stop",
    "χορός": "dance",
    "χόρεψε": "dance",
}


class WallPiRobot:
    def __init__(self):
        logger.info("Initializing WallPi components...")

        # Initialize all subsystems
        self.wake_command = WakeWordDetectorDetector(
            api_key=config.PICOVOICE_API_KEY,
            mic_device_index=config.MIC_DEVICE_INDEX
        )

        self.stt = SpeechToText(
            model_name=config.WHISPER_MODEL,
            mic_device_index=config.MIC_DEVICE_INDEX,
            sample_rate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            chunk=config.CHUNK,
            record_seconds=config.RECORD_SECONDS
        )

        self.brain = ClaudeBrain(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.CLAUDE_MODEL,
            system_prompt=config.SYSTEM_PROMPT,
            max_tokens=config.MAX_TOKENS
        )

        self.tts = TextToSpeech(language=config.TTS_LANGUAGE)

        self.motors = Motors(
            left_in1=config.MOTOR_LEFT_IN1,
            left_in2=config.MOTOR_LEFT_IN2,
            left_pwm=config.MOTOR_LEFT_PWM,
            right_in1=config.MOTOR_RIGHT_IN1,
            right_in2=config.MOTOR_RIGHT_IN2,
            right_pwm=config.MOTOR_RIGHT_PWM,
        )

        logger.info("All components initialized ✅")

    def _handle_movement(self, text: str) -> bool:
        """
        Check if text contains movement commands.
        Returns True if a movement was triggered.
        """
        text_lower = text.lower()
        for keyword, action in MOVE_KEYWORDS.items():
            if keyword in text_lower:
                logger.info(f"🚗 Movement command detected: {action}")
                if action == "forward":
                    self.motors.forward(speed=70, duration=1.5)
                elif action == "backward":
                    self.motors.backward(speed=70, duration=1.5)
                elif action == "left":
                    self.motors.turn_left(speed=60, duration=0.6)
                elif action == "right":
                    self.motors.turn_right(speed=60, duration=0.6)
                elif action == "stop":
                    self.motors.stop()
                elif action == "dance":
                    self.motors.happy_dance()
                return True
        return False

    def process_interaction(self):
        """
        One full interaction cycle:
        1. Record speech
        2. Transcribe
        3. Get Claude response
        4. Speak response
        5. Maybe move
        """
        # Acknowledge wake word with a sound
        self.tts.speak("Ναι;")

        # Record and transcribe user speech
        text = self.stt.listen_and_transcribe()

        if not text or len(text.strip()) < 2:
            self.tts.speak("Δεν σε άκουσα καλά. Ξαναπές το!")
            return

        logger.info(f"User said: '{text}'")

        # Check for movement commands first
        self._handle_movement(text)

        # Get Claude response
        response = self.brain.think(text)

        # Speak the response
        self.tts.speak(response)

        # Happy dance if it's a greeting
        greetings = ["γεια", "hello", "χαίρε", "καλημέρα", "καλησπέρα"]
        if any(g in text.lower() for g in greetings):
            self.motors.happy_dance()

    def startup_sequence(self):
        """Play startup animation and greeting"""
        logger.info("🤖 Running startup sequence...")
        self.motors.happy_dance()
        time.sleep(0.5)
        self.tts.speak(
            "Γεια σου! Είμαι ο Wall-E! Πες 'Hey Walli' για να με ξυπνήσεις!"
        )

    def run(self):
        """Main robot loop"""
        self.startup_sequence()

        logger.info("🔄 Entering main loop...")
        while True:
            try:
                # Wait for wake word
                self.wake_command.listen_for_wake_command()

                # Process the interaction
                self.process_interaction()

                # Small pause before listening again
                time.sleep(0.5)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                self.tts.speak("Ουπς! Κάτι πήγε στραβά!")
                time.sleep(2)

        self.cleanup()

    def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up...")
        self.motors.cleanup()
        self.wake_command.cleanup()
        logger.info("Goodbye! 👋")
