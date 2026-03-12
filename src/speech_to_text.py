"""
Speech-to-Text using faster-whisper (runs locally on Pi).
faster-whisper is optimized for ARM64 and much lighter than openai-whisper.
Records audio after wake command and transcribes it.
"""

import logging
import wave
import tempfile
import os
import pyaudio
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(
        self,
        model_name: str = "base",
        mic_device_index: int = 3,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk: int = 1024,
        record_seconds: int = 7
    ):
        self.model_name = model_name
        self.mic_device_index = mic_device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.record_seconds = record_seconds
        self.model = None

    def _load_model(self):
        """Lazy load faster-whisper model (downloads on first run)"""
        if self.model is None:
            logger.info(f"Loading faster-whisper model '{self.model_name}'...")
            # cpu + int8 = optimal for Raspberry Pi 4
            self.model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8"
            )
            logger.info("faster-whisper model loaded ✅")

    def record_audio(self) -> str:
        """
        Record audio from microphone and save to temp file.
        Returns path to the recorded WAV file.
        """
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.mic_device_index,
            frames_per_buffer=self.chunk
        )

        logger.info(f"🎙️ Recording for {self.record_seconds} seconds...")
        frames = []

        for _ in range(0, int(self.sample_rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()
        logger.info("Recording complete ✅")

        # Save to temp WAV file
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        return tmp.name

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using faster-whisper.
        Returns the transcribed text.
        """
        self._load_model()

        logger.info("🔤 Transcribing audio...")
        segments, info = self.model.transcribe(
            audio_path,
            language="el",          # Greek
            beam_size=3,            # Lower = faster on Pi
            vad_filter=True,        # Skip silence automatically
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Collect all segments into one string
        text = " ".join(segment.text for segment in segments).strip()

        # Cleanup temp file
        os.unlink(audio_path)

        logger.info(f"Transcription: '{text}'")
        return text

    def listen_and_transcribe(self) -> str:
        """
        Record audio and transcribe in one step.
        Returns transcribed text.
        """
        audio_path = self.record_audio()
        return self.transcribe(audio_path)