"""Microphone recording -> in-memory WAV, for speech-to-text via AIService.

Uses sounddevice/PortAudio for capture (free, MIT-licensed, no native
install needed on Windows) and the stdlib `wave` module to encode a WAV
file Groq's Whisper endpoint can transcribe -- no extra audio codec
dependency.
"""
import io
import wave
from typing import List, Optional

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1


class VoiceRecorder:
    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._frames: List[np.ndarray] = []

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self._stream is not None:
            return
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=self._on_audio,
        )
        self._stream.start()

    def _on_audio(self, indata, frames, time_info, status) -> None:
        self._frames.append(indata.copy())

    def stop(self) -> bytes:
        """Stops recording and returns the captured audio as WAV bytes."""
        if self._stream is None:
            return b""
        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._frames:
            return b""

        audio = np.concatenate(self._frames, axis=0)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)  # int16
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio.tobytes())
        return buffer.getvalue()
