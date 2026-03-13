"""
Text-to-Speech for WallPi.
Uses gTTS (Google TTS) for Greek language support, with espeak as offline fallback.

Runs ffplay in a subprocess to avoid PortAudio state conflicts with Porcupine.
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
        """Check if required tools are available."""
        try:
            import gtts
            self.use_gtts = True
            logger.info("Using gTTS for speech synthesis")
        except ImportError:
            self.use_gtts = False
            logger.warning("gTTS not found, falling back to espeak")

    def speak(self, text: str):
        """Convert text to speech and play it."""
        logger.info(f"🔊 Speaking: '{text}'")
        if self.use_gtts:
            self._speak_gtts(text)
        else:
            self._speak_espeak(text)

    def _speak_gtts(self, text: str):
        """
        Use Google TTS (requires internet).
        Saves MP3 to temp file, plays with ffplay via subprocess.
        ffplay runs fully isolated — no shared PortAudio state with Porcupine.
        """
        try:
            from gtts import gTTS

            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()

            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(tmp.name)

            # Run ffplay as a completely separate process.
            # Using subprocess.run (not Popen) ensures it fully exits
            # and releases all audio resources before we return.
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp.name],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except Exception as e:
            logger.error(f"gTTS error: {e}, falling back to espeak")
            self._speak_espeak(text)
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def _speak_espeak(self, text: str):
        """
        Offline fallback using espeak.
        Greek quality is limited but works without internet.
        """
        try:
            subprocess.run(
                ["espeak", "-v", "el", "-s", "150", "-p", "60", text],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.error("espeak not installed. Run: sudo apt install espeak")
        except Exception as e:
            logger.error(f"espeak error: {e}")