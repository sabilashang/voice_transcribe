"""
Main Voice Transcriber Module
Handles speech-to-text conversion with multiple recognition engines
"""

import os
import speech_recognition as sr
import pyaudio
import wave
import threading
import time
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import json
import numpy as np
import librosa
import tempfile
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceTranscriber:
    """Main class for voice transcription functionality"""

    def __init__(self, language: str = 'en-US', engine: str = 'google'):
        """
        Initialize VoiceTranscriber

        Args:
            language: Language code for transcription (default: 'en-US')
            engine: Recognition engine ('google', 'sphinx', 'azure', 'bing')
        """
        self.language = language
        self.engine = engine
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Configure recognizer settings for real-time responsiveness
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6  # Shorter pause for faster response
        self.recognizer.phrase_threshold = 0.2  # More responsive to speech start
        self.recognizer.non_speaking_duration = 0.4  # Faster detection of pauses

        # Advanced settings for better recognition
        self.max_retries = 2  # Retry failed transcriptions
        self.min_confidence = 0.5  # Minimum confidence threshold

        # Chunking settings for large files
        # 20 minutes in seconds (maximum safe duration)
        self.max_chunk_duration = 20 * 60
        self.chunk_warning_threshold = 19 * 60  # 19 minutes - start looking for pauses
        # Minimum pause duration to break at (seconds)
        self.min_pause_duration = 0.5
        self.base_chunk_duration = 30.0  # Base chunk size for normal processing

        # Transcription results storage
        self.transcription_results = []
        self.is_recording = False
        self.recording_thread = None

        logger.info(
            f"VoiceTranscriber initialized with language: {language}, engine: {engine}")

    def calibrate_microphone(self, duration: float = 1.0) -> None:
        """
        Calibrate microphone for ambient noise

        Args:
            duration: Calibration duration in seconds (default: 1.0)
        """
        try:
            logger.info(
                f"Calibrating microphone for ambient noise ({duration}s)...")
            with self.microphone as source:
                # Adjust for ambient noise with specified duration
                self.recognizer.adjust_for_ambient_noise(
                    source, duration=duration)
            logger.info(
                f"Microphone calibration completed. Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            logger.error(f"Microphone calibration failed: {str(e)}")
            raise

    def transcribe_audio_file(self, file_path: str, callback=None, live_display=None) -> Dict[str, any]:
        """
        Transcribe audio from file with chunking support for large files

        Args:
            file_path: Path to audio file
            callback: Optional callback function for progress updates (progress, message)
            live_display: Optional callback function for live text display (text_chunk)

        Returns:
            Dictionary with transcription results
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            logger.info(f"Transcribing audio file: {file_path}")

            if callback:
                callback(0.1, "Loading audio file...")

            # Check if file needs conversion (non-WAV formats)
            file_ext = os.path.splitext(file_path)[1].lower()
            temp_wav_path = None

            if file_ext not in ['.wav']:
                # Convert to WAV format for speech_recognition
                temp_wav_path = self._convert_to_wav(file_path)
                audio_file_path = temp_wav_path
            else:
                audio_file_path = file_path

            # Get audio duration for chunking decision
            try:
                # Try to get duration from the audio file
                import wave
                with wave.open(audio_file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    sample_rate = wf.getframerate()
                    audio_duration = frames / float(sample_rate)
            except:
                # Fallback: use speech_recognition to estimate
                with sr.AudioFile(audio_file_path) as source:
                    audio = self.recognizer.record(source)
                    audio_duration = len(audio.frame_data) / audio.sample_rate if hasattr(
                        audio, 'frame_data') and hasattr(audio, 'sample_rate') else 60

            # For large files (>60 seconds), use chunking with enhancement
            if audio_duration > 60:
                logger.info(
                    f"Large file detected ({audio_duration:.1f}s), using chunking...")
                if callback:
                    callback(
                        0.2, f"Processing large file ({audio_duration:.0f}s)...")

                result = self._transcribe_large_file(
                    audio_file_path, audio_duration, callback, live_display,
                    enhance_audio=True  # Enable audio enhancement
                )
            else:
                # For smaller files, process normally
                if callback:
                    callback(0.3, "Transcribing audio...")

                with sr.AudioFile(audio_file_path) as source:
                    audio = self.recognizer.record(source)

                # Perform transcription
                start_time = time.time()
                text = self._recognize_speech(audio)
                processing_time = time.time() - start_time

                # Remove disfluencies
                if text.strip():
                    text = self._remove_disfluencies(text)

                if callback:
                    callback(0.9, "Finalizing transcription...")

                result = {
                    'file_path': file_path,
                    'text': text,
                    'language': self.language,
                    'engine': self.engine,
                    'processing_time': processing_time,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': None
                }

                if callback:
                    callback(1.0, "Transcription complete!")

            self.transcription_results.append(result)
            logger.info(
                f"Transcription completed in {result['processing_time']:.2f}s")

            # Clean up temporary file
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    logger.debug(f"Cleaned up temporary file: {temp_wav_path}")
                except Exception as e:
                    logger.warning(
                        f"Could not remove temporary file {temp_wav_path}: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Transcription failed for {file_path}: {str(e)}")
            if callback:
                callback(0, f"Error: {str(e)}")
            raise

    def transcribe_realtime(self, duration: int = None, timeout: int = 3) -> Dict[str, any]:
        """
        Perform real-time transcription from microphone with continuous listening

        Args:
            duration: Maximum recording duration in seconds (None for continuous)
            timeout: Timeout for detecting start of speech in seconds

        Returns:
            Dictionary with transcription results
        """
        try:
            logger.info("Starting real-time transcription (continuous mode)")

            # Record audio continuously - listen for natural speech pauses
            with self.microphone as source:
                # Listen for speech - will automatically stop after pause
                if duration:
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=duration
                    )
                else:
                    # Continuous mode - listen until natural pause
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=None  # No limit, stops on pause
                    )

            # Perform transcription immediately
            start_time = time.time()
            text = self._recognize_speech(audio)
            processing_time = time.time() - start_time

            result = {
                'text': text,
                'language': self.language,
                'engine': self.engine,
                'duration': duration,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'confidence': None
            }

            if text.strip():  # Only add non-empty transcriptions
                self.transcription_results.append(result)
                logger.info(f"Real-time transcription: {text[:50]}...")

            return result

        except sr.WaitTimeoutError:
            logger.debug("No speech detected, continuing...")
            return {'text': '', 'error': 'No speech detected'}
        except Exception as e:
            logger.error(f"Real-time transcription failed: {str(e)}")
            return {'text': '', 'error': str(e)}

    def start_continuous_recording(self, callback_func=None) -> None:
        """
        Start continuous recording and transcription

        Args:
            callback_func: Function to call with each transcription result
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return

        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self._continuous_recording_loop,
            args=(callback_func,)
        )
        self.recording_thread.start()
        logger.info("Continuous recording started")

    def stop_continuous_recording(self) -> None:
        """Stop continuous recording"""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return

        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        logger.info("Continuous recording stopped")

    def _continuous_recording_loop(self, callback_func=None) -> None:
        """Internal method for continuous recording loop"""
        try:
            self.calibrate_microphone()

            while self.is_recording:
                try:
                    with self.microphone as source:
                        # Listen for speech with shorter timeout
                        audio = self.recognizer.listen(
                            source, timeout=1, phrase_time_limit=5)

                    # Transcribe the audio
                    text = self._recognize_speech(audio)

                    if text.strip():  # Only process non-empty transcriptions
                        result = {
                            'text': text,
                            'timestamp': datetime.now().isoformat(),
                            'language': self.language,
                            'engine': self.engine
                        }

                        # Call callback function if provided
                        if callback_func:
                            callback_func(result)

                        logger.info(f"Continuous transcription: {text}")

                except sr.WaitTimeoutError:
                    # No speech detected, continue listening
                    continue
                except Exception as e:
                    logger.error(f"Error in continuous recording: {str(e)}")
                    time.sleep(1)  # Brief pause before retrying

        except Exception as e:
            logger.error(f"Continuous recording loop failed: {str(e)}")

    def _recognize_speech(self, audio, retry_on_error: bool = True) -> str:
        """
        Recognize speech using the configured engine with retry logic

        Args:
            audio: Audio data from speech_recognition
            retry_on_error: If True, retry on recognition errors

        Returns:
            Transcribed text
        """
        attempts = 0
        max_attempts = 3 if retry_on_error else 1

        while attempts < max_attempts:
            try:
                if self.engine == 'google':
                    # Use Google with show_all for better accuracy
                    result = self.recognizer.recognize_google(
                        audio, language=self.language, show_all=False)
                    # If result is a dict (show_all=True), extract the text
                    if isinstance(result, dict) and 'alternative' in result:
                        return result['alternative'][0]['transcript']
                    return result if isinstance(result, str) else ""
                elif self.engine == 'sphinx':
                    try:
                        # Sphinx requires pocketsphinx to be installed
                        result = self.recognizer.recognize_sphinx(audio)
                        return result
                    except AttributeError:
                        logger.warning(
                            "Sphinx not available, falling back to Google")
                        # Fallback to Google
                        result = self.recognizer.recognize_google(
                            audio, language=self.language)
                        return result if isinstance(result, str) else ""
                    except OSError as e:
                        logger.warning(
                            f"Sphinx error: {str(e)}, falling back to Google")
                        # Fallback to Google
                        result = self.recognizer.recognize_google(
                            audio, language=self.language)
                        return result if isinstance(result, str) else ""
                elif self.engine == 'azure':
                    # Note: Requires Azure Speech API key
                    return self.recognizer.recognize_azure(audio, language=self.language)
                elif self.engine == 'bing':
                    # Note: Requires Bing Speech API key
                    return self.recognizer.recognize_bing(audio, language=self.language)
                else:
                    raise ValueError(
                        f"Unsupported recognition engine: {self.engine}")

            except sr.UnknownValueError:
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"Recognition attempt {attempts} failed, retrying...")
                    time.sleep(0.5)  # Brief pause before retry
                else:
                    logger.warning(
                        "Speech recognition could not understand audio after all retries")
                    return ""
            except sr.RequestError as e:
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"Service error on attempt {attempts}, retrying...")
                    time.sleep(1)  # Longer pause for service errors
                else:
                    logger.error(f"Speech recognition service error: {str(e)}")
                    raise
            except Exception as e:
                # Catch-all for other errors (like Sphinx not available)
                attempts += 1
                if attempts < max_attempts:
                    logger.warning(
                        f"Unexpected error on attempt {attempts}: {str(e)}, retrying...")
                    time.sleep(1)
                else:
                    logger.error(
                        f"Unexpected error after all retries: {str(e)}")
                    return ""

        return ""

    def get_transcription_history(self) -> List[Dict[str, any]]:
        """Get all transcription results"""
        return self.transcription_results.copy()

    def clear_history(self) -> None:
        """Clear transcription history"""
        self.transcription_results.clear()
        logger.info("Transcription history cleared")

    def export_transcriptions(self, file_path: str, format: str = 'json') -> None:
        """
        Export transcription results to file

        Args:
            file_path: Output file path
            format: Export format ('json', 'txt', 'csv')
        """
        try:
            if format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.transcription_results, f,
                              indent=2, ensure_ascii=False)

            elif format == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    for i, result in enumerate(self.transcription_results):
                        f.write(f"Transcription {i+1}:\n")
                        f.write(
                            f"Timestamp: {result.get('timestamp', 'N/A')}\n")
                        f.write(f"Text: {result.get('text', '')}\n")
                        f.write("-" * 50 + "\n")

            elif format == 'csv':
                import pandas as pd
                df = pd.DataFrame(self.transcription_results)
                df.to_csv(file_path, index=False)

            else:
                raise ValueError(f"Unsupported export format: {format}")

            logger.info(
                f"Transcriptions exported to {file_path} in {format} format")

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise

    def set_language(self, language: str) -> None:
        """Change transcription language"""
        self.language = language
        logger.info(f"Language changed to: {language}")

    def set_engine(self, engine: str) -> None:
        """Change recognition engine"""
        if engine not in ['google', 'sphinx', 'azure', 'bing']:
            raise ValueError(f"Unsupported engine: {engine}")

        self.engine = engine
        logger.info(f"Recognition engine changed to: {engine}")

    def _find_pause_in_audio(self, audio_file_path: str, start_time: float, end_time: float, sample_rate: int = 16000) -> Optional[float]:
        """
        Find the next pause (silence) in audio segment for natural chunking

        Args:
            audio_file_path: Path to audio file
            start_time: Start time in seconds to search from
            end_time: End time in seconds to search until
            sample_rate: Sample rate of audio

        Returns:
            Time position of pause (in seconds) or None if no pause found
        """
        try:
            # Load audio segment
            audio_data, sr = librosa.load(audio_file_path, sr=sample_rate,
                                          offset=start_time, duration=end_time - start_time)

            if len(audio_data) == 0:
                return None

            # Calculate frame-based energy for pause detection
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop

            # Compute RMS energy for each frame
            rms = librosa.feature.rms(y=audio_data, frame_length=frame_length,
                                      hop_length=hop_length)[0]

            # Threshold for silence detection (adaptive)
            silence_threshold = np.mean(rms) * 0.15

            # Find pauses (regions below threshold)
            pause_frames = np.where(rms < silence_threshold)[0]

            if len(pause_frames) == 0:
                return None

            # Look for pauses longer than minimum duration
            min_pause_frames = int(self.min_pause_duration * sr / hop_length)

            # Find continuous pause segments
            pause_segments = []
            in_pause = False
            pause_start = 0

            for i, frame_idx in enumerate(pause_frames):
                if i == 0 or pause_frames[i] != pause_frames[i-1] + 1:
                    # New pause segment
                    if in_pause:
                        pause_duration = (
                            pause_frames[i-1] - pause_start) * hop_length / sr
                        if pause_duration >= self.min_pause_duration:
                            pause_segments.append((pause_start * hop_length / sr,
                                                   pause_frames[i-1] * hop_length / sr))
                    pause_start = frame_idx
                    in_pause = True
                elif i == len(pause_frames) - 1:
                    # End of pause
                    pause_duration = (
                        frame_idx - pause_start) * hop_length / sr
                    if pause_duration >= self.min_pause_duration:
                        pause_segments.append((pause_start * hop_length / sr,
                                               frame_idx * hop_length / sr))

            # Return the first pause position (closest to start)
            if pause_segments:
                return start_time + pause_segments[0][0]

            return None

        except Exception as e:
            logger.warning(f"Error finding pause: {str(e)}")
            return None

    def _remove_disfluencies(self, text: str) -> str:
        """
        Remove common disfluencies from transcribed text

        Args:
            text: Input text with potential disfluencies

        Returns:
            Cleaned text without disfluencies
        """
        # Common disfluencies to remove
        disfluencies = [
            r'\bum\b', r'\buh\b', r'\ber\b', r'\berm\b', r'\beh\b',
            r'\buhm\b', r'\buhh\b', r'\bumm\b', r'\buhmm\b',
            r'\blike\s+like\b', r'\byou\s+know\s+you\s+know\b',
            r'\bwell\s+well\b', r'\bso\s+so\b'
        ]

        cleaned_text = text

        # Remove disfluencies (case-insensitive)
        for pattern in disfluencies:
            cleaned_text = re.sub(
                pattern, '', cleaned_text, flags=re.IGNORECASE)

        # Clean up multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        # Remove leading/trailing spaces
        cleaned_text = cleaned_text.strip()

        return cleaned_text

    def _transcribe_large_file(self, audio_file_path: str, duration: float, callback=None, live_display=None, enhance_audio: bool = True) -> Dict[str, any]:
        """
        Transcribe large audio files using intelligent pause-based chunking
        Breaks audio at natural pauses when approaching time limits (19-20 minutes)

        Args:
            audio_file_path: Path to WAV audio file
            duration: Duration of the audio file in seconds
            callback: Optional callback function for progress updates
            live_display: Optional callback function for live text display (text_chunk)
            enhance_audio: If True, apply audio enhancement for better accuracy

        Returns:
            Dictionary with transcription results
        """
        try:
            full_text = []
            start_time = time.time()
            offset = 0.0
            chunk_num = 0

            # Estimate total chunks for progress tracking
            estimated_chunks = max(
                1, int(duration / self.base_chunk_duration) + 1)

            logger.info(
                f"Processing large file ({duration:.1f}s) with pause-based chunking")

            # Open audio file once and process in chunks
            with sr.AudioFile(audio_file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # Get sample rate for pause detection
                sample_rate = source.SAMPLE_RATE

                while offset < duration:
                    try:
                        # Calculate time elapsed in current "super-chunk" (for pause detection)
                        # Track cumulative time to detect when approaching 19-20 minute limits
                        cumulative_time = offset
                        time_since_last_break = cumulative_time % self.max_chunk_duration
                        remaining_to_limit = self.max_chunk_duration - time_since_last_break

                        # Determine chunk duration based on proximity to limit
                        if remaining_to_limit < 60 and time_since_last_break >= self.chunk_warning_threshold:
                            # We're approaching the 19-20 minute limit - look for pauses
                            # Try to find a pause to break at within the next minute
                            search_end = min(
                                offset + remaining_to_limit + 30, duration)
                            pause_position = self._find_pause_in_audio(
                                audio_file_path, offset, search_end, sample_rate)

                            if pause_position and pause_position > offset:
                                # Found a pause - use it as chunk boundary
                                chunk_duration = pause_position - offset
                                logger.info(
                                    f"Found pause at {pause_position:.1f}s (approaching limit), breaking chunk at {chunk_duration:.1f}s")
                            else:
                                # No pause found, use remaining time or base chunk
                                chunk_duration = min(
                                    remaining_to_limit, self.base_chunk_duration)
                                logger.info(
                                    f"No pause found near limit, using {chunk_duration:.1f}s chunk")
                        else:
                            # Normal chunking - use base chunk size
                            chunk_duration = min(
                                self.base_chunk_duration, duration - offset)

                        # Ensure we don't exceed remaining duration
                        chunk_duration = min(chunk_duration, duration - offset)

                        if chunk_duration <= 0:
                            break

                        # Update progress
                        progress = 0.2 + (offset / duration) * 0.7
                        if callback:
                            callback(
                                progress, f"Processing chunk {chunk_num + 1} ({chunk_duration:.1f}s at {offset:.1f}s)...")

                        # Record chunk - stream advances naturally, do NOT pass offset
                        audio = self.recognizer.record(
                            source, duration=chunk_duration)

                        # Transcribe chunk
                        text = self._recognize_speech(audio)

                        # Remove disfluencies
                        if text.strip():
                            text = self._remove_disfluencies(text)
                            full_text.append(text)
                            logger.info(
                                f"Chunk {chunk_num + 1} transcribed ({chunk_duration:.1f}s): {text[:50]}...")

                            # Display text live if callback provided
                            if live_display:
                                # Add space between chunks
                                live_display(text + " ")

                        # Move to next chunk
                        offset += chunk_duration
                        chunk_num += 1

                    except sr.UnknownValueError:
                        # Don't skip - keep retrying this chunk up to 3 times
                        retry_count = 0
                        max_retries = 3
                        chunk_succeeded = False

                        while retry_count < max_retries and not chunk_succeeded:
                            retry_count += 1
                            logger.warning(
                                f"Could not transcribe chunk {chunk_num + 1}, retry {retry_count}/{max_retries}...")
                            # Exponential backoff
                            time.sleep(0.5 * retry_count)

                            try:
                                # Recalculate chunk duration for retry
                                time_since_last_break = offset % self.max_chunk_duration
                                remaining_to_limit = self.max_chunk_duration - time_since_last_break

                                if remaining_to_limit < 60 and time_since_last_break >= self.chunk_warning_threshold:
                                    chunk_duration_retry = min(
                                        remaining_to_limit, self.base_chunk_duration)
                                else:
                                    chunk_duration_retry = min(
                                        self.base_chunk_duration, duration - offset)

                                chunk_duration_retry = min(
                                    chunk_duration_retry, duration - offset)

                                # Try again - stream already advanced, can't re-read same chunk
                                audio = self.recognizer.record(
                                    source, duration=chunk_duration_retry)
                                text = self._recognize_speech(
                                    audio, retry_on_error=False)

                                if text.strip():
                                    text = self._remove_disfluencies(text)
                                    full_text.append(text)
                                    logger.info(
                                        f"Chunk {chunk_num + 1} succeeded on retry {retry_count}")
                                    chunk_succeeded = True

                                    # Display text live if callback provided
                                    if live_display:
                                        live_display(text + " ")
                            except:
                                if retry_count >= max_retries:
                                    logger.error(
                                        f"Chunk {chunk_num + 1} failed after {max_retries} retries, skipping")
                                    break

                        # Move to next chunk only if succeeded or exhausted retries
                        if chunk_succeeded:
                            # Recalculate chunk duration for moving forward
                            time_since_last_break = offset % self.max_chunk_duration
                            remaining_to_limit = self.max_chunk_duration - time_since_last_break

                            if remaining_to_limit < 60 and time_since_last_break >= self.chunk_warning_threshold:
                                chunk_duration = min(
                                    remaining_to_limit, self.base_chunk_duration)
                            else:
                                chunk_duration = min(
                                    self.base_chunk_duration, duration - offset)

                            chunk_duration = min(
                                chunk_duration, duration - offset)
                            offset += chunk_duration
                            chunk_num += 1
                        elif retry_count >= max_retries:
                            # Skip failed chunk and move forward
                            offset += min(self.base_chunk_duration,
                                          duration - offset)
                            chunk_num += 1
                        continue

                    except Exception as e:
                        # For other errors, retry up to 3 times
                        retry_count = 0
                        max_retries = 3
                        chunk_succeeded = False

                        while retry_count < max_retries and not chunk_succeeded:
                            retry_count += 1
                            logger.error(
                                f"Error transcribing chunk {chunk_num + 1}: {str(e)}, retry {retry_count}/{max_retries}")
                            time.sleep(1 * retry_count)  # Exponential backoff

                            try:
                                # Recalculate chunk duration for retry
                                time_since_last_break = offset % self.max_chunk_duration
                                remaining_to_limit = self.max_chunk_duration - time_since_last_break

                                if remaining_to_limit < 60 and time_since_last_break >= self.chunk_warning_threshold:
                                    chunk_duration_retry = min(
                                        remaining_to_limit, self.base_chunk_duration)
                                else:
                                    chunk_duration_retry = min(
                                        self.base_chunk_duration, duration - offset)

                                chunk_duration_retry = min(
                                    chunk_duration_retry, duration - offset)

                                audio = self.recognizer.record(
                                    source, duration=chunk_duration_retry)
                                text = self._recognize_speech(
                                    audio, retry_on_error=False)

                                if text.strip():
                                    text = self._remove_disfluencies(text)
                                    full_text.append(text)
                                    logger.info(
                                        f"Chunk {chunk_num + 1} succeeded on retry {retry_count}")
                                    chunk_succeeded = True

                                    if live_display:
                                        live_display(text + " ")
                            except Exception as retry_error:
                                if retry_count >= max_retries:
                                    logger.error(
                                        f"Chunk {chunk_num + 1} failed after {max_retries} retries")
                                    break

                        if chunk_succeeded:
                            # Recalculate chunk duration for moving forward
                            time_since_last_break = offset % self.max_chunk_duration
                            remaining_to_limit = self.max_chunk_duration - time_since_last_break

                            if remaining_to_limit < 60 and time_since_last_break >= self.chunk_warning_threshold:
                                chunk_duration = min(
                                    remaining_to_limit, self.base_chunk_duration)
                            else:
                                chunk_duration = min(
                                    self.base_chunk_duration, duration - offset)

                            chunk_duration = min(
                                chunk_duration, duration - offset)
                            offset += chunk_duration
                            chunk_num += 1
                        elif retry_count >= max_retries:
                            # Skip failed chunk and move forward
                            offset += min(self.base_chunk_duration,
                                          duration - offset)
                            chunk_num += 1
                        continue

            # Combine all chunks and apply final disfluency removal
            combined_text = " ".join(full_text)
            combined_text = self._remove_disfluencies(combined_text)
            processing_time = time.time() - start_time

            if callback:
                callback(0.95, "Finalizing results...")

            result = {
                'file_path': audio_file_path,
                'text': combined_text,
                'language': self.language,
                'engine': self.engine,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'confidence': None,
                'chunks_processed': chunk_num
            }

            if callback:
                callback(1.0, "Transcription complete!")

            return result

        except Exception as e:
            logger.error(f"Large file transcription failed: {str(e)}")
            raise

    def _convert_to_wav(self, file_path: str) -> str:
        """
        Convert audio file to WAV format for speech_recognition compatibility
        with automatic audio enhancement

        Args:
            file_path: Path to input audio file

        Returns:
            Path to temporary WAV file
        """
        try:
            import tempfile
            from pydub import AudioSegment
            from pydub.effects import normalize

            # Create temporary WAV file
            temp_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)  # Close file descriptor, we only need the path

            logger.info(
                f"Converting {file_path} to WAV format with enhancement...")

            # Load audio file using pydub
            audio = AudioSegment.from_file(file_path)

            # Apply automatic volume normalization
            audio = normalize(audio)

            # Auto-boost quiet audio
            if audio.rms < 1000:  # Audio is quiet
                boost_db = min(20, 2000 / audio.rms if audio.rms > 0 else 20)
                audio = audio + boost_db
                logger.info(
                    f"Auto-boosting audio by {boost_db:.1f}dB (RMS: {audio.rms:.1f})")

            # Convert to WAV format with appropriate parameters
            audio.export(temp_wav_path, format="wav")

            logger.info(f"Successfully converted to: {temp_wav_path}")
            return temp_wav_path

        except Exception as e:
            logger.error(f"Failed to convert {file_path} to WAV: {str(e)}")
            # Provide helpful error message
            if "ffmpeg" in str(e).lower() or "winerror 2" in str(e).lower():
                raise ValueError(f"Cannot process .m4a files without ffmpeg. Please install ffmpeg:\n"
                                 f"1. Download from https://ffmpeg.org/download.html\n"
                                 f"2. Extract to C:\\ffmpeg\\\n"
                                 f"3. Add C:\\ffmpeg\\bin to your system PATH\n"
                                 f"Original error: {str(e)}")
            else:
                raise ValueError(
                    f"Could not convert audio file to WAV format: {str(e)}")


def main():
    """Demo function to test VoiceTranscriber"""
    transcriber = VoiceTranscriber()

    print("VoiceTranscriber initialized successfully!")
    print(f"Language: {transcriber.language}")
    print(f"Engine: {transcriber.engine}")

    # Test with a sample audio file (if available)
    # transcriber.transcribe_audio_file("sample.wav")


if __name__ == "__main__":
    main()
