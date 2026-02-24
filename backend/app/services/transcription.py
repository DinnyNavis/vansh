"""
Transcription Service — OpenAI Whisper API integration.
Handles audio file transcription for both direct audio uploads
and audio extracted from video files.
"""

import os
import logging
from openai import OpenAI
from .local_transcription import LocalTranscriptionService

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Transcribes audio files using OpenAI Whisper API with Local Fallback."""

    SUPPORTED_FORMATS = {"wav", "mp3", "webm", "ogg", "m4a", "flac", "mp4"}

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.local_fallback = LocalTranscriptionService()

    def transcribe(self, file_path, language=None):
        """
        Transcribe an audio file with OpenAI (Primary) and Local (Fallback).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {ext}")

        # 1. Primary: OpenAI Whisper API
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"Attempting OpenAI Whisper (Primary): {file_path} ({file_size_mb:.1f} MB)")
            
            with open(file_path, "rb") as audio_file:
                # Crystal-Clear Transcription Guide: Direct Whisper to be highly literal and handle Thanglish/Mixed speech.
                thanglish_prompt = (
                    "Transcribe the following audio with CRYSTAL CLEAR VERBATIM ACCURACY. "
                    "The narration may be lively, fast-paced, and heavily code-switched (Thanglish/Hinglish/Regional mixes). "
                    "Handle phrases like: 'naan Chennai-la valarndhen', 'amma romba happy', 'naan engineer aayitten', 'seri okay da'. "
                    "CRITICAL: USE ROMAN SCRIPT (English letters) ONLY. No Unicode scripts (no தமிழ், etc.). "
                    "Capture every single word, including regional fillers (la, da, pa, na), exactly as spoken. "
                    "This is for a professional biography, so accuracy of the phonetics is paramount."
                )

                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "prompt": thanglish_prompt, # Guide Whisper for code-switching
                }
                if language:
                    params["language"] = language

                response = self.client.audio.transcriptions.create(**params)

            logger.info(f"OpenAI Transcription complete: {len(response.text)} chars")
            return {
                "text": response.text,
                "duration": getattr(response, "duration", 0),
                "source": "openai"
            }

        except Exception as e:
            logger.warning(f"OpenAI Transcription failed: {e}. Switching to Local Fallback...")
            
            # 2. Fallback: Local Faster-Whisper
            try:
                result = self.local_fallback.transcribe(file_path)
                logger.info(f"Local Transcription complete: {len(result['text'])} chars")
                return {
                    "text": result["text"],
                    "duration": 0,  # Local doesn't provide total duration easily in same format
                    "source": "local"
                }
            except Exception as local_e:
                logger.error(f"All transcription methods failed: {local_e}")
                raise
