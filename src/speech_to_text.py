"""
Speech-to-Text using OpenAI Whisper (runs locally on Pi).
Records audio after wake word and transcribes it.
"""

import logging
import wave
import tempfile
import os
import pyaudio
import whisper

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
        """Lazy load Whisper model (takes a few seconds first time)"""
        if self.model is None:
            logger.info(f"Loading Whisper model '{self.model_name}'...")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded ✅")

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
        Transcribe audio file to text using Whisper.
        Returns the transcribed text.
        """
        self._load_model()

        logger.info("🔤 Transcribing audio...")
        result = self.model.transcribe(
            audio_path,
            language="el",       # Greek
            fp16=False,          # Pi 4 doesn't have GPU
            verbose=False
        )

        # Cleanup temp file
        os.unlink(audio_path)

        text = result["text"].strip()
        logger.info(f"Transcription: '{text}'")
        return text

    def listen_and_transcribe(self) -> str:
        """
        Record audio and transcribe in one step.
        Returns transcribed text.
        """
        audio_path = self.record_audio()
        return self.transcribe(audio_path)
