"""
Wake word detection using Picovoice Porcupine.
Listens for 'Hey Google' (built-in) or custom 'Hey Walli' keyword.
"""

import logging
import struct
import os
import ctypes

# Suppress ALSA/JACK error spam before importing pyaudio
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int,
    ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
)
def _py_error_handler(filename, line, function, err, fmt):
    pass  # Silence all ALSA errors

try:
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    asound.snd_lib_error_set_handler(ERROR_HANDLER_FUNC(_py_error_handler))
except Exception:
    pass

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

    def _find_input_device(self) -> int:
        """Find the correct input device index for PyAudio."""
        audio = pyaudio.PyAudio()
        target = self.mic_device_index

        # Try to find device by matching the card index
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                name = info.get("name", "").lower()
                logger.info(f"Input device {i}: {name}")
                if "usb" in name or "pnp" in name:
                    target = i
                    logger.info(f"Using USB mic at PyAudio device index {i}")
                    break

        audio.terminate()
        return target

    def _init_porcupine(self):
        """Initialize Porcupine with built-in or custom keyword."""
        try:
            custom_keyword = os.path.join(
                os.path.dirname(__file__), "..", "hey-walli.ppn"
            )
            if os.path.exists(custom_keyword):
                self.porcupine = pvporcupine.create(
                    access_key=self.api_key,
                    keyword_paths=[custom_keyword],
                    sensitivities=[0.7]
                )
                logger.info("Using custom 'Hey Walli' wake word ✅")
            else:
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
        """Initialize PyAudio stream with correct device."""
        device_index = self._find_input_device()
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.porcupine.frame_length
        )
        logger.info(f"Porcupine audio stream opened on device {device_index} ✅")

    def listen_for_wake_word(self) -> bool:
        """Block until wake word is detected. Returns True when detected."""
        if self.porcupine is None:
            self._init_porcupine()
            self._init_audio()

        logger.info("👂 Listening for wake word...")

        while True:
            pcm = self.stream.read(
                self.porcupine.frame_length,
                exception_on_overflow=False
            )
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(pcm)

            if keyword_index >= 0:
                logger.info("🎯 Wake word detected!")
                return True

    def cleanup(self):
        """Release all resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        if self.porcupine:
            self.porcupine.delete()
        logger.info("WakeWordDetector cleaned up")