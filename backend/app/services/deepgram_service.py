"""
Deepgram Transcription Service — High-speed, high-accuracy audio transcription.
"""

import os
import logging
from deepgram import DeepgramClient

logger = logging.getLogger(__name__)

class DeepgramService:
    def __init__(self, api_key):
        self.api_key = api_key
        if not self.api_key:
            logger.warning("Deepgram API Key is missing. Transcription will fail.")
        self.client = DeepgramClient(self.api_key)

    def transcribe(self, file_path):
        """Transcribe an audio file using Deepgram."""
        if not self.api_key:
            raise ValueError("Deepgram API Key is not configured")

        try:
            with open(file_path, "rb") as file:
                buffer_data = file.read()

            payload = {
                "buffer": buffer_data,
            }

            options = {
                "model": "nova-2",
                "smart_format": True,
                "paragraphs": True,
                "language": "en", # Deepgram performs best with 'en' + keywords for code-switching
                "detect_language": True,
                "keywords": [
                    "naan:3", "poren:3", "amma:3", "appa:3", "seri:3", "epdi:3", "romba:3", 
                    "konjam:3", "vaanga:3", "ponga:3", "anna:3", "thambi:3", "paaru:3",
                    "la:2", "da:2", "na:2", "pa:2", "valarndhen:3", "aayitten:3", "illai:2"
                ]
            }

            response = self.client.listen.prerecorded.v("1").transcribe_file(payload, options)
            
            # Extract transcript
            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            
            return {
                "text": transcript,
                "raw": response
            }
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {e}")
            raise

    def start_live_transcription(self, on_message, on_error=None, on_open=None, on_close=None):
        """
        Start a live transcription session.
        Returns a connection object that audio chunks can be sent to.
        """
        if not self.api_key:
            raise ValueError("Deepgram API Key is not configured")

        from deepgram import LiveOptions, LiveTranscriptionEvents

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            container="webm", # Explicitly handle webm/opus stream from browser
            smart_format=True,
            interim_results=True,
            utterance_end_ms="1000",
            keywords=[
                "naan:3", "poren:3", "amma:3", "appa:3", "seri:3", "epdi:3", "romba:3", 
                "konjam:3", "vaanga:3", "ponga:3", "anna:3", "thambi:3", "paaru:3",
                "la:2", "da:2", "na:2", "pa:2", "valarndhen:3", "aayitten:3", "illai:2"
            ]
        )

        try:
            dg_connection = self.client.listen.live.v("1")

            def on_message_handler(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if transcript:
                    on_message(transcript, is_final=result.is_final)

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message_handler)
            
            if on_error:
                dg_connection.on(LiveTranscriptionEvents.Error, lambda self, error, **kwargs: on_error(error))
            if on_open:
                dg_connection.on(LiveTranscriptionEvents.Open, lambda self, open, **kwargs: on_open(open))
            if on_close:
                dg_connection.on(LiveTranscriptionEvents.Close, lambda self, close, **kwargs: on_close(close))

            dg_connection.start(options)
            return dg_connection

        except Exception as e:
            logger.error(f"Failed to start Deepgram live session: {e}")
            raise
