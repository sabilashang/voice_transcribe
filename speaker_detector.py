"""
Speaker Detection and Voice Identification Module
Handles speaker diarization, voice clustering, and speaker identification
"""

import os
import numpy as np
import librosa
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import json
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeakerDetector:
    """Handles speaker detection, diarization, and voice identification"""

    def __init__(self, sample_rate: int = 16000):
        """
        Initialize SpeakerDetector

        Args:
            sample_rate: Audio sample rate for processing
        """
        self.sample_rate = sample_rate
        self.speaker_profiles = {}
        self.voice_features_cache = {}

        logger.info("SpeakerDetector initialized")

    def extract_voice_features(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Extract voice features from audio data

        Args:
            audio_data: Audio data as numpy array

        Returns:
            Feature vector representing voice characteristics
        """
        try:
            features = []

            # 1. MFCC (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(
                y=audio_data, sr=self.sample_rate, n_mfcc=13)
            features.extend(np.mean(mfccs, axis=1))
            features.extend(np.std(mfccs, axis=1))

            # 2. Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=self.sample_rate)
            # Use append for scalar
            features.append(np.mean(spectral_centroids))
            # Use append for scalar
            features.append(np.std(spectral_centroids))

            # 3. Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_data)
            features.append(np.mean(zcr))  # Use append for scalar
            features.append(np.std(zcr))   # Use append for scalar

            # 4. Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(
                y=audio_data, sr=self.sample_rate)
            features.append(np.mean(rolloff))  # Use append for scalar
            features.append(np.std(rolloff))   # Use append for scalar

            # 5. Chroma features
            chroma = librosa.feature.chroma_stft(
                y=audio_data, sr=self.sample_rate)
            features.extend(np.mean(chroma, axis=1))

            # 6. Tonnetz features
            tonnetz = librosa.feature.tonnetz(
                y=audio_data, sr=self.sample_rate)
            features.extend(np.mean(tonnetz, axis=1))

            # 7. Rhythm features
            try:
                tempo, beats = librosa.beat.beat_track(
                    y=audio_data, sr=self.sample_rate)
                features.append(tempo if np.isscalar(tempo) else float(tempo))
            except Exception as e:
                # If beat tracking fails, use a default tempo
                logger.warning(
                    f"Beat tracking failed: {str(e)}, using default tempo")
                features.append(120.0)  # Default tempo

            return np.array(features)

        except Exception as e:
            logger.error(f"Error extracting voice features: {str(e)}")
            raise

    def segment_audio_by_silence(self, audio_data: np.ndarray, min_silence_duration: float = 0.5) -> List[Tuple[int, int]]:
        """
        Segment audio into speech segments based on silence detection

        Args:
            audio_data: Input audio data
            min_silence_duration: Minimum silence duration to split segments

        Returns:
            List of (start, end) sample indices for speech segments
        """
        try:
            # Calculate frame-based energy
            frame_length = int(0.025 * self.sample_rate)  # 25ms frames
            hop_length = int(0.010 * self.sample_rate)    # 10ms hop

            # Compute RMS energy for each frame
            rms = librosa.feature.rms(
                y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]

            # Threshold for silence detection
            silence_threshold = np.mean(rms) * 0.1

            # Find speech segments
            speech_segments = []
            in_speech = False
            start_frame = 0

            for i, energy in enumerate(rms):
                if energy > silence_threshold and not in_speech:
                    start_frame = i
                    in_speech = True
                elif energy <= silence_threshold and in_speech:
                    # Check if silence duration is long enough to split
                    silence_duration = (i - start_frame) * \
                        hop_length / self.sample_rate
                    if silence_duration >= min_silence_duration:
                        end_frame = i
                        start_sample = start_frame * hop_length
                        end_sample = end_frame * hop_length
                        speech_segments.append((start_sample, end_sample))
                        in_speech = False

            # Handle case where audio ends during speech
            if in_speech:
                end_sample = len(audio_data)
                start_sample = start_frame * hop_length
                speech_segments.append((start_sample, end_sample))

            logger.info(f"Found {len(speech_segments)} speech segments")
            return speech_segments

        except Exception as e:
            logger.error(f"Error segmenting audio: {str(e)}")
            raise

    def detect_speakers(self, audio_data: np.ndarray, max_speakers: int = 5) -> Dict[str, any]:
        """
        Detect and identify different speakers in audio

        Args:
            audio_data: Input audio data
            max_speakers: Maximum number of speakers to detect

        Returns:
            Dictionary with speaker detection results
        """
        try:
            logger.info("Starting speaker detection...")

            # Segment audio into speech segments
            speech_segments = self.segment_audio_by_silence(audio_data)

            if len(speech_segments) < 2:
                logger.warning(
                    "Not enough speech segments for speaker detection")
                return {
                    'speakers': [],
                    'segments': [],
                    'error': 'Insufficient speech segments'
                }

            # Extract features for each segment
            segment_features = []
            segment_info = []

            for i, (start, end) in enumerate(speech_segments):
                segment_audio = audio_data[start:end]

                # Skip very short segments
                if len(segment_audio) < 0.5 * self.sample_rate:  # Less than 0.5 seconds
                    continue

                features = self.extract_voice_features(segment_audio)
                segment_features.append(features)
                segment_info.append({
                    'segment_id': i,
                    'start_time': start / self.sample_rate,
                    'end_time': end / self.sample_rate,
                    'duration': (end - start) / self.sample_rate,
                    'start_sample': start,
                    'end_sample': end
                })

            if len(segment_features) < 2:
                logger.warning(
                    "Not enough valid segments for speaker detection")
                return {
                    'speakers': [],
                    'segments': segment_info,
                    'error': 'Insufficient valid segments'
                }

            # Normalize features
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(segment_features)

            # Determine optimal number of speakers using silhouette analysis
            optimal_speakers = self._find_optimal_speakers(
                normalized_features, max_speakers)

            # Perform speaker clustering
            speaker_labels = self._cluster_speakers(
                normalized_features, optimal_speakers)

            # Organize results
            speakers = {}
            for i, label in enumerate(speaker_labels):
                speaker_id = f"Speaker_{label + 1}"

                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        'speaker_id': speaker_id,
                        'segments': [],
                        'total_duration': 0,
                        'feature_vector': segment_features[i]
                    }

                speakers[speaker_id]['segments'].append(segment_info[i])
                speakers[speaker_id]['total_duration'] += segment_info[i]['duration']

            # Convert to list format
            speaker_list = list(speakers.values())

            result = {
                'speakers': speaker_list,
                'total_speakers': len(speaker_list),
                'segments': segment_info,
                'processing_time': datetime.now().isoformat(),
                'method': 'clustering'
            }

            logger.info(f"Detected {len(speaker_list)} speakers")
            return result

        except Exception as e:
            logger.error(f"Speaker detection failed: {str(e)}")
            raise

    def _find_optimal_speakers(self, features: np.ndarray, max_speakers: int) -> int:
        """
        Find optimal number of speakers using silhouette analysis

        Args:
            features: Normalized feature matrix
            max_speakers: Maximum number of speakers to consider

        Returns:
            Optimal number of speakers
        """
        try:
            if len(features) < 2:
                return 1

            max_clusters = min(max_speakers, len(features) - 1)
            silhouette_scores = []

            for n_clusters in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=n_clusters,
                                random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(features)
                score = silhouette_score(features, cluster_labels)
                silhouette_scores.append(score)

            if not silhouette_scores:
                return 2

            optimal_clusters = np.argmax(silhouette_scores) + 2
            logger.info(f"Optimal number of speakers: {optimal_clusters}")

            return optimal_clusters

        except Exception as e:
            logger.warning(
                f"Error finding optimal speakers: {str(e)}, using default")
            return 2

    def _cluster_speakers(self, features: np.ndarray, n_speakers: int) -> List[int]:
        """
        Cluster speakers using K-means algorithm

        Args:
            features: Normalized feature matrix
            n_speakers: Number of speakers to cluster

        Returns:
            List of speaker labels for each segment
        """
        try:
            if n_speakers == 1:
                return [0] * len(features)

            # Use K-means clustering
            kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features)

            return labels.tolist()

        except Exception as e:
            logger.error(f"Speaker clustering failed: {str(e)}")
            raise

    def create_speaker_profile(self, audio_data: np.ndarray, speaker_name: str) -> Dict[str, any]:
        """
        Create a speaker profile from audio data

        Args:
            audio_data: Audio data for the speaker
            speaker_name: Name/ID for the speaker

        Returns:
            Speaker profile dictionary
        """
        try:
            features = self.extract_voice_features(audio_data)

            profile = {
                'speaker_name': speaker_name,
                'feature_vector': features.tolist(),
                'created_at': datetime.now().isoformat(),
                'sample_rate': self.sample_rate
            }

            self.speaker_profiles[speaker_name] = profile
            logger.info(f"Created speaker profile for: {speaker_name}")

            return profile

        except Exception as e:
            logger.error(f"Error creating speaker profile: {str(e)}")
            raise

    def identify_speaker(self, audio_data: np.ndarray) -> Dict[str, any]:
        """
        Identify speaker from audio data using existing profiles

        Args:
            audio_data: Audio data to identify

        Returns:
            Identification results
        """
        try:
            if not self.speaker_profiles:
                return {
                    'identified_speaker': None,
                    'confidence': 0,
                    'error': 'No speaker profiles available'
                }

            # Extract features from input audio
            input_features = self.extract_voice_features(audio_data)

            # Compare with existing profiles
            similarities = {}
            for speaker_name, profile in self.speaker_profiles.items():
                profile_features = np.array(profile['feature_vector'])

                # Calculate cosine similarity
                similarity = np.dot(input_features, profile_features) / (
                    np.linalg.norm(input_features) *
                    np.linalg.norm(profile_features)
                )
                similarities[speaker_name] = similarity

            # Find best match
            best_speaker = max(similarities, key=similarities.get)
            best_confidence = similarities[best_speaker]

            result = {
                'identified_speaker': best_speaker,
                'confidence': float(best_confidence),
                'all_similarities': similarities
            }

            logger.info(
                f"Identified speaker: {best_speaker} (confidence: {best_confidence:.3f})")
            return result

        except Exception as e:
            logger.error(f"Speaker identification failed: {str(e)}")
            raise

    def save_speaker_profiles(self, file_path: str) -> None:
        """Save speaker profiles to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.speaker_profiles, f,
                          indent=2, ensure_ascii=False)
            logger.info(f"Speaker profiles saved to: {file_path}")
        except Exception as e:
            logger.error(f"Error saving speaker profiles: {str(e)}")
            raise

    def load_speaker_profiles(self, file_path: str) -> None:
        """Load speaker profiles from file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.speaker_profiles = json.load(f)
                logger.info(f"Speaker profiles loaded from: {file_path}")
            else:
                logger.warning(f"Speaker profiles file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading speaker profiles: {str(e)}")
            raise

    def get_speaker_statistics(self, detection_result: Dict[str, any]) -> Dict[str, any]:
        """
        Generate statistics from speaker detection results

        Args:
            detection_result: Results from detect_speakers method

        Returns:
            Statistics dictionary
        """
        try:
            speakers = detection_result.get('speakers', [])

            if not speakers:
                return {'error': 'No speakers detected'}

            stats = {
                'total_speakers': len(speakers),
                'total_duration': sum(speaker['total_duration'] for speaker in speakers),
                'speaker_details': []
            }

            for speaker in speakers:
                speaker_stats = {
                    'speaker_id': speaker['speaker_id'],
                    'segment_count': len(speaker['segments']),
                    'total_duration': speaker['total_duration'],
                    'average_segment_duration': speaker['total_duration'] / len(speaker['segments']) if speaker['segments'] else 0,
                    'speaking_percentage': (speaker['total_duration'] / stats['total_duration']) * 100 if stats['total_duration'] > 0 else 0
                }
                stats['speaker_details'].append(speaker_stats)

            return stats

        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}")
            raise


def main():
    """Demo function to test SpeakerDetector"""
    detector = SpeakerDetector()

    print("SpeakerDetector initialized successfully!")
    print(f"Sample rate: {detector.sample_rate}")

    # Test with sample audio (if available)
    # audio_data, sr = librosa.load("sample.wav", sr=16000)
    # result = detector.detect_speakers(audio_data)
    # print(f"Detected {result['total_speakers']} speakers")


if __name__ == "__main__":
    main()
