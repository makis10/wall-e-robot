"""
Wake command detection using Picovoice Porcupine.
Listens for 'Hey Google' (built-in) or custom 'Hey Walli' keyword.

Audio pipeline: mic runs at 44100Hz (native), resampled to 16000Hz for Porcupine.
Stream is released after wake command detection so STT can use the mic.
"""

import logging
import os

import numpy as np
import soxr
import pyaudio
import pvporcupine

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
        self._resample_buffer = np.array([], dtype=np.int16)

    def _find_usb_device(self, audio: pyaudio.PyAudio) -> int:
        """
        Find USB mic device index using an existing PyAudio instance.
        Never creates or terminates PyAudio here — caller owns the instance.
        """
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

        return target

    def _init_porcupine(self):
        """Initialize Porcupine with built-in or custom keyword."""
        if self.porcupine is not None:
            return  # Already initialized, reuse it

        custom_keyword = os.path.join(
            os.path.dirname(__file__), "..", "hey-walli.ppn"
        )
        if os.path.exists(custom_keyword):
            self.porcupine = pvporcupine.create(
                access_key=self.api_key,
                keyword_paths=[custom_keyword],
                sensitivities=[1.0]
            )
            logger.info("Using custom 'Hey Walli' wake command ✅")
        else:
            self.porcupine = pvporcupine.create(
                access_key=self.api_key,
                keywords=["hey google"],
                sensitivities=[1.0]
            )
            logger.warning(
                "Custom keyword not found. Using 'Hey Google' as wake command. "
                "Download 'Hey Walli' from https://console.picovoice.ai/"
            )

    def _open_stream(self):
        """Open mic stream. Called before listening, closed after detection."""
        self.audio = pyaudio.PyAudio()
        device_index = self._find_usb_device(self.audio)

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
        # Reset buffer on each new stream open
        self._resample_buffer = np.array([], dtype=np.int16)
        logger.info(
            f"Audio stream: device={device_index}, "
            f"{NATIVE_RATE}Hz → {self.porcupine.sample_rate}Hz (soxr resample) ✅"
        )

    def _close_stream(self):
        """
        Close mic stream and release PyAudio.
        Must be called after wake command detection so STT can use the mic.
        """
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        if self.audio:
            self.audio.terminate()
            self.audio = None
        logger.info("Mic released for STT ✅")

    def _read_resampled_frame(self) -> list:
        """
        Read raw 44100Hz audio, resample to 16000Hz via soxr,
        buffer and return exactly porcupine.frame_length int16 samples.
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
        """
        Block until wake command is detected.
        Opens mic stream on entry, closes it on detection so STT can use the mic.
        Returns True when detected.
        """
        self._init_porcupine()
        self._open_stream()

        logger.info("👂 Listening for wake command...")

        try:
            while True:
                pcm = self._read_resampled_frame()
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    logger.info("🎯 Wake command detected!")
                    return True
        finally:
            # Always release mic so STT can open it
            self._close_stream()

    def cleanup(self):
        """Release all resources."""
        self._close_stream()
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        logger.info("WakeCommandDetector cleaned up")
