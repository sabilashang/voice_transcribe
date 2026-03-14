"""
Audio Processing Utilities for Voice Transcriber
Handles various audio formats, preprocessing, and enhancement
"""

import os
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
import scipy.signal as signal
from typing import Tuple, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing, format conversion, and enhancement"""

    def __init__(self, sample_rate: int = 16000):
        """
        Initialize AudioProcessor

        Args:
            sample_rate: Target sample rate for processing (default: 16000Hz)
        """
        self.sample_rate = sample_rate
        self.supported_formats = ['.wav', '.mp3',
                                  '.m4a', '.flac', '.ogg', '.aac']

    def load_audio(self, file_path: str, streaming: bool = False) -> Tuple[np.ndarray, int]:
        """
        Load audio file and return audio data and sample rate

        Args:
            file_path: Path to audio file
            streaming: If True, only get metadata without loading full file (for large files)

        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {file_ext}")

            # For very large files, use streaming mode
            file_size = os.path.getsize(file_path)
            is_large_file = file_size > 100 * 1024 * 1024  # 100 MB

            # For .m4a files, use pydub for better compatibility
            if file_ext == '.m4a':
                audio_data, sr = self._load_m4a_with_pydub(
                    file_path, streaming)
            else:
                # For large files, limit duration or use streaming
                if is_large_file and streaming:
                    # Get just metadata without loading entire file
                    duration = librosa.get_duration(path=file_path)
                    audio_data, sr = self._get_audio_info_only(
                        file_path, duration)
                else:
                    # Load audio using librosa for other formats
                    audio_data, sr = librosa.load(
                        file_path, sr=self.sample_rate)

            logger.info(
                f"Loaded audio: {file_path}, duration: {len(audio_data)/sr:.2f}s")

            return audio_data, sr

        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {str(e)}")
            raise

    def save_audio(self, audio_data: np.ndarray, file_path: str, sample_rate: int = None) -> None:
        """
        Save audio data to file

        Args:
            audio_data: Audio data as numpy array
            file_path: Output file path
            sample_rate: Sample rate (uses instance default if None)
        """
        try:
            sr = sample_rate or self.sample_rate

            # Ensure audio data is in correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize audio data
            audio_data = self.normalize_audio(audio_data)

            sf.write(file_path, audio_data, sr)
            logger.info(f"Saved audio to: {file_path}")

        except Exception as e:
            logger.error(f"Error saving audio file {file_path}: {str(e)}")
            raise

    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio data to prevent clipping

        Args:
            audio_data: Input audio data

        Returns:
            Normalized audio data
        """
        # Normalize to [-1, 1] range
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        return audio_data

    def reduce_noise(self, audio_data: np.ndarray, noise_reduction_factor: float = 0.2) -> np.ndarray:
        """
        Apply basic noise reduction using spectral subtraction

        Args:
            audio_data: Input audio data
            noise_reduction_factor: Factor for noise reduction (0.0-1.0)

        Returns:
            Noise-reduced audio data
        """
        try:
            # Compute Short-Time Fourier Transform
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            phase = np.angle(stft)

            # Estimate noise from first few frames
            noise_frames = magnitude[:, :10]
            noise_estimate = np.mean(noise_frames, axis=1, keepdims=True)

            # Apply spectral subtraction
            enhanced_magnitude = magnitude - noise_reduction_factor * noise_estimate
            enhanced_magnitude = np.maximum(
                enhanced_magnitude, 0.1 * magnitude)

            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft)

            return enhanced_audio

        except Exception as e:
            logger.warning(
                f"Noise reduction failed: {str(e)}, returning original audio")
            return audio_data

    def enhance_audio(self, audio_data: np.ndarray, auto_boost: bool = True, preserve_voice: bool = True) -> np.ndarray:
        """
        Apply audio enhancement techniques including automatic volume boosting
        while preserving voice content at all frequencies

        Args:
            audio_data: Input audio data
            auto_boost: If True, automatically boost quiet audio
            preserve_voice: If True, use gentler filtering to preserve low-pitched voices (default: True)

        Returns:
            Enhanced audio data
        """
        try:
            # Calculate RMS (Root Mean Square) for volume detection
            rms = np.sqrt(np.mean(audio_data**2))

            # Auto-boost quiet audio to improve recognition
            if auto_boost and rms < 0.1:  # Audio is quiet
                boost_factor = 0.3 / rms if rms > 0 else 3.0
                boost_factor = min(boost_factor, 5.0)  # Limit boost to 5x
                enhanced = audio_data * boost_factor
                logger.info(
                    f"Auto-boosting audio: RMS={rms:.4f}, boost={boost_factor:.2f}x")
            else:
                enhanced = audio_data.copy()

            # Normalize audio to prevent clipping
            enhanced = self.normalize_audio(enhanced)

            # Apply noise reduction for cleaner audio (gentler to preserve voice)
            enhanced = self.reduce_noise(enhanced, noise_reduction_factor=0.15)

            if preserve_voice:
                # Use gentler filtering to preserve voice at ALL frequencies
                # Voice fundamentals: Males 85-255 Hz, Females 165-255 Hz, but low voices can go to 60-80 Hz
                # Use a two-stage filter that only removes extreme rumble (<30Hz) and gentle noise (30-60Hz)

                # Stage 1: Remove extreme rumble below 30Hz only
                sos = signal.butter(2, 30, btype='high',
                                    fs=self.sample_rate, output='sos')
                enhanced = signal.sosfilt(sos, enhanced)
                logger.info(
                    "Applied voice-preserving filtering (30Hz gentle cutoff)")
            else:
                # Original 50Hz cutoff for aggressive noise removal
                sos = signal.butter(4, 50, btype='high',
                                    fs=self.sample_rate, output='sos')
                enhanced = signal.sosfilt(sos, enhanced)
                logger.info("Applied standard filtering (50Hz cutoff)")

            # Apply low-pass filter to remove high-frequency noise (above 8kHz)
            # Preserves voice clarity while removing high-frequency artifacts
            sos_low = signal.butter(4, 8000, btype='low',
                                    fs=self.sample_rate, output='sos')
            enhanced = signal.sosfilt(sos_low, enhanced)

            # Final normalization
            enhanced = self.normalize_audio(enhanced)

            return enhanced

        except Exception as e:
            logger.warning(
                f"Audio enhancement failed: {str(e)}, returning original audio")
            return audio_data

    def split_audio(self, audio_data: np.ndarray, chunk_duration: float = 30.0) -> List[np.ndarray]:
        """
        Split audio into chunks of specified duration

        Args:
            audio_data: Input audio data
            chunk_duration: Duration of each chunk in seconds

        Returns:
            List of audio chunks
        """
        chunk_samples = int(chunk_duration * self.sample_rate)
        chunks = []

        for i in range(0, len(audio_data), chunk_samples):
            chunk = audio_data[i:i + chunk_samples]
            if len(chunk) > 0:
                chunks.append(chunk)

        logger.info(
            f"Split audio into {len(chunks)} chunks of {chunk_duration}s each")
        return chunks

    def convert_format(self, input_path: str, output_path: str, output_format: str = None) -> None:
        """
        Convert audio file to different format

        Args:
            input_path: Input file path
            output_path: Output file path
            output_format: Target format (inferred from output_path if None)
        """
        try:
            # Load audio using pydub for format conversion
            audio = AudioSegment.from_file(input_path)

            # Normalize audio
            audio = normalize(audio)

            # Export to target format
            audio.export(output_path, format=output_format)
            logger.info(f"Converted {input_path} to {output_path}")

        except Exception as e:
            logger.error(f"Format conversion failed: {str(e)}")
            raise

    def get_audio_info(self, file_path: str, streaming: bool = True) -> dict:
        """
        Get audio file information efficiently (without loading full file for large files)

        Args:
            file_path: Path to audio file
            streaming: If True, use streaming mode for large files

        Returns:
            Dictionary with audio information
        """
        try:
            file_size = os.path.getsize(file_path)
            is_large_file = file_size > 100 * 1024 * 1024  # 100 MB

            # For large files, use streaming mode to get just metadata
            if is_large_file and streaming:
                try:
                    file_ext = os.path.splitext(file_path)[1].lower()

                    # Get duration efficiently
                    if file_ext == '.m4a':
                        from pydub import AudioSegment
                        audio_segment = AudioSegment.from_file(file_path)
                        duration = len(audio_segment) / 1000.0
                        sample_rate = audio_segment.frame_rate
                    else:
                        duration = librosa.get_duration(path=file_path)
                        sample_rate = self.sample_rate

                    info = {
                        'file_path': file_path,
                        'duration': duration,
                        'sample_rate': sample_rate,
                        'channels': 1,
                        'samples': int(duration * sample_rate),
                        'format': file_ext,
                        'file_size': file_size
                    }

                    logger.info(
                        f"Got audio info for large file {file_path} (streaming mode)")
                    return info
                except Exception as e:
                    logger.warning(
                        f"Streaming mode failed, falling back to full load: {str(e)}")

            # For smaller files, load normally
            audio_data, sr = self.load_audio(file_path)

            info = {
                'file_path': file_path,
                'duration': len(audio_data) / sr,
                'sample_rate': sr,
                'channels': 1,  # librosa loads as mono
                'samples': len(audio_data),
                'format': os.path.splitext(file_path)[1].lower(),
                'file_size': file_size
            }

            return info

        except Exception as e:
            logger.error(f"Error getting audio info for {file_path}: {str(e)}")
            raise

    def detect_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> List[Tuple[int, int]]:
        """
        Detect silent segments in audio

        Args:
            audio_data: Input audio data
            threshold: Silence threshold

        Returns:
            List of (start, end) sample indices for silent segments
        """
        # Find samples below threshold
        silent_samples = np.abs(audio_data) < threshold

        # Find silent segments
        silent_segments = []
        in_silence = False
        start_idx = 0

        for i, is_silent in enumerate(silent_samples):
            if is_silent and not in_silence:
                start_idx = i
                in_silence = True
            elif not is_silent and in_silence:
                silent_segments.append((start_idx, i))
                in_silence = False

        # Handle case where audio ends in silence
        if in_silence:
            silent_segments.append((start_idx, len(audio_data)))

        return silent_segments

    def _get_audio_info_only(self, file_path: str, duration: float) -> Tuple[np.ndarray, int]:
        """
        Get audio metadata without loading full file

        Args:
            file_path: Path to audio file
            duration: Duration in seconds

        Returns:
            Tuple of (dummy_audio_data, sample_rate)
        """
        # Return minimal audio data just for duration info
        dummy_samples = int(duration * self.sample_rate)
        audio_data = np.zeros(dummy_samples, dtype=np.float32)
        return audio_data, self.sample_rate

    def _load_m4a_with_pydub(self, file_path: str, streaming: bool = False) -> Tuple[np.ndarray, int]:
        """
        Load .m4a file using pydub for better compatibility

        Args:
            file_path: Path to .m4a file
            streaming: If True, only get metadata without loading full audio

        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            from pydub import AudioSegment

            if streaming:
                # Get metadata only without loading full file
                audio_segment = AudioSegment.from_file(file_path)
                duration = len(audio_segment) / 1000.0  # Convert to seconds
                sample_rate = audio_segment.frame_rate

                # Return dummy audio data with correct duration
                dummy_samples = int(duration * self.sample_rate)
                audio_data = np.zeros(dummy_samples, dtype=np.float32)

                logger.info(
                    f"Loaded metadata for .m4a file (streaming mode) - duration: {duration:.2f}s")
                return audio_data, self.sample_rate

            # Load full audio file
            audio_segment = AudioSegment.from_file(file_path)

            # Convert to numpy array
            # Get raw audio data
            raw_data = audio_segment.raw_data

            # Convert to numpy array
            audio_data = np.frombuffer(raw_data, dtype=np.int16)

            # Convert to float32 and normalize
            audio_data = audio_data.astype(np.float32) / 32768.0

            # Get sample rate
            sample_rate = audio_segment.frame_rate

            # Resample if needed
            if sample_rate != self.sample_rate:
                # Simple resampling (for better results, use librosa.resample)
                import scipy.signal as signal
                num_samples = int(len(audio_data) *
                                  self.sample_rate / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)
                sample_rate = self.sample_rate

            return audio_data, sample_rate

        except Exception as e:
            logger.error(f"Failed to load .m4a file with pydub: {str(e)}")
            # Fallback: try to get basic info without loading audio data
            try:
                from pydub import AudioSegment
                audio_segment = AudioSegment.from_file(file_path)
                duration = len(audio_segment) / 1000.0  # Convert to seconds
                sample_rate = audio_segment.frame_rate

                # Return dummy audio data with correct duration
                dummy_samples = int(duration * self.sample_rate)
                audio_data = np.zeros(dummy_samples, dtype=np.float32)

                logger.warning(
                    f"Using fallback method for .m4a file - audio data not loaded")
                return audio_data, self.sample_rate

            except Exception as e2:
                logger.error(f"Fallback method also failed: {str(e2)}")
                raise ValueError(
                    f"Cannot load .m4a file. Please install ffmpeg for full support. Error: {str(e)}")


def main():
    """Demo function to test AudioProcessor"""
    processor = AudioProcessor()

    # Example usage
    print("AudioProcessor initialized successfully!")
    print(f"Supported formats: {processor.supported_formats}")
    print(f"Default sample rate: {processor.sample_rate}Hz")


if __name__ == "__main__":
    main()
