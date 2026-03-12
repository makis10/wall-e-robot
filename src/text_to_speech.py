"""
Text-to-Speech for WallPi.
Uses gTTS (Google TTS) for Greek language support,
with pyttsx3 as offline fallback.
"""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(self, language: str = "el"):
        self.language = language
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required tools are available"""
        try:
            import gtts
            self.use_gtts = True
            logger.info("Using gTTS for speech synthesis")
        except ImportError:
            self.use_gtts = False
            logger.warning("gTTS not found, falling back to espeak")

    def speak(self, text: str):
        """
        Convert text to speech and play it.
        Tries gTTS first (better Greek), falls back to espeak.
        """
        logger.info(f"🔊 Speaking: '{text}'")

        if self.use_gtts:
            self._speak_gtts(text)
        else:
            self._speak_espeak(text)

    def _speak_gtts(self, text: str):
        """Use Google TTS (requires internet)"""
        try:
            from gtts import gTTS

            # Save to temp file
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(tmp.name)

            # Play with ffplay (part of ffmpeg)
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp.name],
                check=True
            )

            os.unlink(tmp.name)

        except Exception as e:
            logger.error(f"gTTS error: {e}, falling back to espeak")
            self._speak_espeak(text)

    def _speak_espeak(self, text: str):
        """
        Offline fallback using espeak.
        Greek quality is limited but works without internet.
        """
        try:
            subprocess.run(
                ["espeak", "-v", "el", "-s", "150", "-p", "60", text],
                check=True,
                capture_output=True
            )
        except FileNotFoundError:
            logger.error("espeak not installed. Run: sudo apt install espeak")
        except Exception as e:
            logger.error(f"espeak error: {e}")

    def play_startup_sound(self):
        """Play a Wall-E style startup beep sequence"""
        try:
            # Generate beeps using speaker-test or sox
            beeps = [
                ("600", "0.1"), ("800", "0.1"),
                ("1000", "0.15"), ("800", "0.1"), ("1200", "0.2")
            ]
            for freq, duration in beeps:
                subprocess.run(
                    ["speaker-test", "-t", "sine", "-f", freq,
                     "-l", "1", "-p", duration],
                    capture_output=True, timeout=1
                )
        except Exception:
            pass  # Beeps are optional, don't crash if they fail
