"""
Local Transcription Service — Uses Faster-Whisper for 4x speed increase.
No API key required.
"""

import os
import logging
import torch
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class LocalTranscriptionService:
    def __init__(self, model_size="large-v3-turbo"):
        """
        Initialize with Faster-Whisper.
        Models: 'tiny', 'base', 'small', 'medium', 'large-v3', 'large-v3-turbo'
        'large-v3-turbo' is the best balance of speed and accuracy.
        """
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Determine compute type based on hardware
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        logger.info(f"Local Transcription initialized on {self.device} with {self.compute_type}")

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading Faster-Whisper model: {self.model_size} on {self.device}...")
            # Faster-Whisper initialization
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )

    def transcribe(self, file_path):
        """Transcribe an audio file locally using Faster-Whisper."""
        try:
            self._load_model()
            logger.info(f"Locally transcribing (Faster-Whisper): {file_path}")
            
            # initial_prompt primes Whisper with vocabulary context for code-switching.
            multilingual_hint = (
                "The speaker is using Thanglish (Tamil and English mixed), Hinglish (Hindi and English), or other South Asian code-switched speech. "
                "CRITICAL: Always transcribe in Roman/Phonetic English alphabet only. "
                "DO NOT use Tamil Unicode characters (e.g. தமிழ்) or any other non-Latin scripts. "
                "Examples of phonetic transcription to follow: 'I went to school la', 'Amma romba happy', 'Naan engineer aayitten', 'Enaku puriyala'. "
                "Preserve all markers like la, da, na, pa, dei, machan exactly as they are spoken. "
                "The goal is a verbatim, literal phonetic transcription in English letters."
            )
            
            # transcription returns a generator and info
            segments, info = self.model.transcribe(
                file_path,
                beam_size=5,
                language=None, # auto-detect
                initial_prompt=multilingual_hint,
                vad_filter=True, # Voice Activity Detection to skip silence
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            
            # Join segments into full text
            full_text = []
            segment_list = []
            for segment in segments:
                # Post-Transcription Cleaning: Ensure Roman-only even if prompt fails
                segment_text = segment.text
                if any(ord(c) > 127 for c in segment_text): # Detect Unicode/Tamil script
                    # If local transcription still outputs Unicode, it's considered junk
                    # but we keep it for the NLP layer to attempt a 'Rescue'
                    pass
                
                full_text.append(segment_text)
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment_text
                })
            
            return {
                "text": " ".join(full_text).strip(),
                "language": info.language,
                "segments": segment_list
            }
        except Exception as e:
            logger.error(f"Faster-Whisper transcription error: {e}")
            raise Exception(f"Local transcription failed: {str(e)}")

