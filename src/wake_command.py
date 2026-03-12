"""
Wake word detection using Picovoice Porcupine.
Listens for 'Hey Walli' (using 'Hey Siri' as closest built-in keyword,
or a custom keyword file if available).
"""

import logging
import struct
import pyaudio
import pvporcupine

logger = logging.getLogger(__name__)


class WakeWordDetector:
    def __init__(self, api_key: str, mic_device_index: int = 3):
        self.api_key = api_key
        self.mic_device_index = mic_device_index
        self.porcupine = None
        self.audio = None
        self.stream = None

    def _init_porcupine(self):
        """Initialize Porcupine with built-in 'Hey Google' keyword as fallback.
        For production, use a custom 'Hey Walli' keyword from Picovoice Console.
        """
        try:
            # Try using a custom keyword file first (hey-walli.ppn)
            import os
            custom_keyword = os.path.join(
                os.path.dirname(__file__), "..", "hey-walli.ppn"
            )
            if os.path.exists(custom_keyword):
                self.porcupine = pvporcupine.create(
                    access_key=self.api_key,
                    keyword_paths=[custom_keyword],
                    sensitivities=[0.7]
                )
                logger.info("Using custom 'Hey Walli' wake word")
            else:
                # Fallback to built-in keyword
                self.porcupine = pvporcupine.create(
                    access_key=self.api_key,
                    keywords=["hey google"],
                    sensitivities=[0.5]
                )
                logger.warning(
                    "Custom keyword not found. Using 'Hey Google' as wake word. "
                    "Download 'Hey Walli' from https://console.picovoice.ai/"
                )
        except Exception as e:
            logger.error(f"Failed to init Porcupine: {e}")
            raise

    def _init_audio(self):
        """Initialize PyAudio stream"""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=self.mic_device_index,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen_for_wake_word(self) -> bool:
        """
        Block until wake word is detected.
        Returns True when detected.
        """
        if self.porcupine is None:
            self._init_porcupine()
            self._init_audio()

        logger.info("👂 Listening for wake word...")

        while True:
            pcm = self.stream.read(
                self.porcupine.frame_length,
                exception_on_overflow=False
            )
            pcm = struct.unpack_from(
                "h" * self.porcupine.frame_length, pcm
            )
            keyword_index = self.porcupine.process(pcm)

            if keyword_index >= 0:
                logger.info("🎯 Wake word detected!")
                return True

    def cleanup(self):
        """Release all resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        if self.porcupine:
            self.porcupine.delete()
        logger.info("WakeWordDetector cleaned up")
