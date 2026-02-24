"""
Video Processor Service — MoviePy-based audio extraction from video files.
"""

import os
import logging
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)


class VideoProcessorService:
    """Extracts audio from video files using MoviePy."""

    SUPPORTED_FORMATS = {"mp4", "mov", "avi", "mkv", "webm"}

    def extract_audio(self, video_path, output_format="wav"):
        """
        Extract audio track from a video file using MoviePy.

        Args:
            video_path: Path to the video file
            output_format: Output audio format (wav, mp3)

        Returns:
            str: Path to the extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        ext = video_path.rsplit(".", 1)[-1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported video format: {ext}")

        # Generate output path
        base = video_path.rsplit(".", 1)[0]
        audio_path = f"{base}_audio.{output_format}"

        logger.info(f"Extracting audio from {video_path} using MoviePy...")

        video_clip = None
        try:
            video_clip = VideoFileClip(video_path)
            
            # Extract audio and save
            # We use 16000Hz mono as it's optimal for transcription models
            video_clip.audio.write_audiofile(
                audio_path,
                fps=16000,
                nbytes=2,
                codec='pcm_s16le' if output_format == "wav" else 'libmp3lame',
            )

            logger.info(f"Audio extracted successfully to {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"MoviePy audio extraction failed: {e}")
            raise RuntimeError(f"Failed to extract audio using MoviePy: {str(e)}")
        finally:
            # Important: Close the clips to release file handles
            if video_clip:
                try:
                    video_clip.close()
                except:
                    pass
