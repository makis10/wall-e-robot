"""
Speech-to-Text using faster-whisper (runs locally on Pi).
faster-whisper is optimized for ARM64 and much lighter than openai-whisper.

Records audio at 44100Hz (USB mic native rate) and transcribes with Whisper.
Whisper accepts any sample rate — no resampling needed here.
"""

import logging
import wave
import tempfile
import os
import pyaudio

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

NATIVE_RATE = 44100  # USB PnP mic native sample rate


class SpeechToText:
    def __init__(
        self,
        model_name: str = "base",
        mic_device_index: int = 3,
        sample_rate: int = 16000,   # Kept for API compatibility, not used for recording
        channels: int = 1,
        chunk: int = 1024,
        record_seconds: int = 7
    ):
        self.model_name = model_name
        self.mic_device_index = mic_device_index
        self.channels = channels
        self.chunk = chunk
        self.record_seconds = record_seconds
        self.model = None

    def _load_model(self):
        """Lazy-load faster-whisper model (downloads on first run)."""
        if self.model is None:
            logger.info(f"Loading faster-whisper '{self.model_name}'...")
            # cpu + int8 = optimal for Raspberry Pi 4
            self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
            logger.info("faster-whisper loaded ✅")

    def _find_input_device(self) -> int:
        """Find USB mic PyAudio device index by name."""
        audio = pyaudio.PyAudio()
        target = 1  # Safe fallback

        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                name = info.get("name", "").lower()
                if "usb" in name or "pnp" in name:
                    target = i
                    logger.info(f"STT: Using USB mic at PyAudio device {i}")
                    break

        audio.terminate()
        return target

    def record_audio(self) -> str:
        """
        Record audio from mic at native 44100Hz.
        Saves to a temp WAV file and returns its path.
        Whisper handles any sample rate internally.
        """
        audio = pyaudio.PyAudio()
        device_index = self._find_input_device()

        # Get sample size before opening stream (needed for WAV header)
        sample_width = audio.get_sample_size(pyaudio.paInt16)

        stream = audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=NATIVE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk
        )

        logger.info(f"🎙️ Recording {self.record_seconds}s at {NATIVE_RATE}Hz...")
        frames = []
        total_chunks = int(NATIVE_RATE / self.chunk * self.record_seconds)

        for _ in range(total_chunks):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()
        logger.info("Recording complete ✅")

        # Save to temp WAV — sample_width captured before terminate()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(NATIVE_RATE)
            wf.writeframes(b"".join(frames))

        return tmp.name

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe WAV file to Greek text using faster-whisper.
        Returns the transcribed string.
        """
        self._load_model()

        logger.info("🔤 Transcribing...")
        segments, _ = self.model.transcribe(
            audio_path,
            language="el",      # Greek
            beam_size=3,        # Lower = faster on Pi
            vad_filter=True,    # Skip silence automatically
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text = " ".join(seg.text for seg in segments).strip()
        os.unlink(audio_path)

        logger.info(f"Transcription: '{text}'")
        return text

    def listen_and_transcribe(self) -> str:
        """Record and transcribe in one step."""
        return self.transcribe(self.record_audio())