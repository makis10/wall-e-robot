"""
Wake command detection using Picovoice Porcupine.
Listens for 'Hey Google' (built-in) or custom 'Hey Walli' keyword.

Audio pipeline: mic runs at 44100Hz (native), resampled to 16000Hz for Porcupine.
"""

import logging
import os
import ctypes

import numpy as np
import soxr
import pyaudio
import pvporcupine

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

logger = logging.getLogger(__name__)

NATIVE_RATE = 44100  # USB PnP mic native sample rate


class WakeCommandDetector:
    def __init__(self, api_key: str, mic_device_index: int = 3):
        self.api_key = api_key
        self.mic_device_index = mic_device_index
        self.porcupine = None
        self.audio = None
        self.stream = None
        self.native_chunk = None
        # Accumulates resampled samples until we have a full porcupine frame
        self._resample_buffer = np.array([], dtype=np.int16)

    def _find_input_device(self) -> int:
        """Find USB mic PyAudio device index by name."""
        audio = pyaudio.PyAudio()
        target = 1  # Safe fallback

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
        custom_keyword = os.path.join(
            os.path.dirname(__file__), "..", "hey-walli.ppn"
        )
        if os.path.exists(custom_keyword):
            self.porcupine = pvporcupine.create(
                access_key=self.api_key,
                keyword_paths=[custom_keyword],
                sensitivities=[0.7]
            )
            logger.info("Using custom 'Hey Walli' wake command ✅")
        else:
            self.porcupine = pvporcupine.create(
                access_key=self.api_key,
                keywords=["hey google"],
                sensitivities=[0.5]
            )
            logger.warning(
                "Custom keyword not found. Using 'Hey Google' as wake command. "
                "Download 'Hey Walli' from https://console.picovoice.ai/"
            )

    def _init_audio(self):
        """
        Open mic at native 44100Hz.
        Porcupine needs 16000Hz — we resample each chunk in software.
        native_chunk: how many 44100Hz frames equal one porcupine frame at 16000Hz.
        """
        device_index = self._find_input_device()
        self.audio = pyaudio.PyAudio()

        self.native_chunk = int(
            self.porcupine.frame_length * NATIVE_RATE / self.porcupine.sample_rate
        ) + 1

        self.stream = self.audio.open(
            rate=NATIVE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.native_chunk
        )
        logger.info(
            f"Audio stream: device={device_index}, "
            f"{NATIVE_RATE}Hz → {self.porcupine.sample_rate}Hz (soxr resample) ✅"
        )

    def _read_resampled_frame(self) -> list:
        """
        Read raw audio at 44100Hz, resample to 16000Hz via soxr,
        buffer samples and return exactly porcupine.frame_length int16 values.
        """
        while len(self._resample_buffer) < self.porcupine.frame_length:
            raw = self.stream.read(self.native_chunk, exception_on_overflow=False)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            resampled = soxr.resample(samples, NATIVE_RATE, self.porcupine.sample_rate)
            self._resample_buffer = np.concatenate(
                [self._resample_buffer, resampled.astype(np.int16)]
            )

        frame = self._resample_buffer[:self.porcupine.frame_length]
        self._resample_buffer = self._resample_buffer[self.porcupine.frame_length:]
        return frame.tolist()

    def listen_for_wake_command(self) -> bool:
        """Block until wake command is detected. Returns True when detected."""
        if self.porcupine is None:
            self._init_porcupine()
            self._init_audio()

        logger.info("👂 Listening for wake command...")

        while True:
            pcm = self._read_resampled_frame()
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                logger.info("🎯 Wake command detected!")
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
        logger.info("WakeCommandDetector cleaned up")