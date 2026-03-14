"""
GUI Interface for Voice Transcriber with Speaker Detection
Modern, user-friendly interface with soft milk palette and micro-interactions
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import customtkinter as ctk
import threading
import os
from datetime import datetime
import json
from typing import Optional, Callable
import time
import logging
import speech_recognition as sr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our custom modules
from voice_transcriber import VoiceTranscriber
from speaker_detector import SpeakerDetector
from audio_processor import AudioProcessor

# Configure customtkinter with soft milk theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Neumorphism/Liquid Glass Color Palette
COLORS = {
    'bg_primary': '#F8FAFC',        # Soft white background
    'bg_secondary': '#FFFFFF',       # Pure white cards
    'bg_tertiary': '#F1F5F9',       # Light gray for subtle areas
    'accent_primary': '#3B82F6',    # Soft blue
    'accent_secondary': '#8B5CF6',   # Soft purple
    'accent_success': '#10B981',     # Soft green
    'accent_warning': '#F59E0B',     # Soft orange
    'accent_error': '#EF4444',       # Soft red
    'text_primary': '#1E293B',       # Dark slate
    'text_secondary': '#64748B',     # Medium slate
    'text_light': '#94A3B8',         # Light slate
    'border_light': '#E2E8F0',       # Very light border
    'shadow_light': '#CBD5E1',       # Light shadow
    'glass_white': 'rgba(255, 255, 255, 0.8)',  # Glass effect
    'glass_overlay': 'rgba(255, 255, 255, 0.1)',  # Overlay effect
    # Legacy color mappings for backward compatibility
    'primary': '#F8FAFC',
    'secondary': '#FFFFFF',
    'accent': '#3B82F6',
    'text': '#1E293B',
    'text_light': '#94A3B8',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'border': '#E2E8F0',
    'hover': '#F1F5F9',
    'active': '#E2E8F0'
}


class VoiceTranscriberGUI:
    """Main GUI application for Voice Transcriber with Neumorphism/Liquid Glass theme"""

    def __init__(self):
        """Initialize the GUI application"""
        self.root = ctk.CTk()
        self.root.title("🎤 Troice - Neumorphism UI")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)

        # Configure root window with neumorphism theme
        self.root.configure(fg_color=COLORS['bg_primary'])

        # Initialize components
        self.transcriber = VoiceTranscriber()
        self.speaker_detector = SpeakerDetector()
        self.audio_processor = AudioProcessor()

        # GUI state variables
        self.is_recording = False
        self.is_paused = False
        self.continuous_recording_active = False
        self.current_file = None
        self.file_queue = []  # Optional queue for multiple files
        self.transcription_results = []
        self.speaker_results = None
        self.animation_running = False
        self.live_transcription_active = False
        self.live_text_buffer = ""

        # Typing animation variables
        self.typing_index = 0
        self.typing_text = ""

        # Create custom styles
        self.create_custom_styles()

        # Create GUI elements
        self.create_widgets()
        self.setup_layout()

        # Load speaker profiles if they exist
        self.load_speaker_profiles()

        # Start micro-interactions
        self.setup_micro_interactions()

    def create_custom_styles(self):
        """Create custom styles for the neumorphism/liquid glass theme"""
        # Configure customtkinter colors
        ctk.set_default_color_theme("blue")

        # Neumorphism button styles
        self.neumorphism_button_style = {
            'fg_color': COLORS['bg_secondary'],
            'hover_color': COLORS['bg_tertiary'],
            'text_color': COLORS['text_primary'],
            'corner_radius': 20,
            'border_width': 0,
            'font': ctk.CTkFont(size=14, weight="normal")
        }

        self.primary_button_style = {
            'fg_color': COLORS['accent_primary'],
            'hover_color': '#2563EB',
            'text_color': 'white',
            'corner_radius': 25,
            'border_width': 0,
            'font': ctk.CTkFont(size=16, weight="bold")
        }

        self.success_button_style = {
            'fg_color': COLORS['accent_success'],
            'hover_color': '#059669',
            'text_color': 'white',
            'corner_radius': 25,
            'border_width': 0,
            'font': ctk.CTkFont(size=16, weight="bold")
        }

        self.error_button_style = {
            'fg_color': COLORS['accent_error'],
            'hover_color': '#DC2626',
            'text_color': 'white',
            'corner_radius': 25,
            'border_width': 0,
            'font': ctk.CTkFont(size=16, weight="bold")
        }

        self.warning_button_style = {
            'fg_color': COLORS['accent_warning'],
            'hover_color': '#D97706',
            'text_color': 'white',
            'corner_radius': 25,
            'border_width': 0,
            'font': ctk.CTkFont(size=16, weight="bold")
        }

        # Neumorphism frame styles
        self.neumorphism_frame_style = {
            'fg_color': COLORS['bg_secondary'],
            'corner_radius': 25,
            'border_width': 0
        }

        self.glass_frame_style = {
            'fg_color': COLORS['bg_secondary'],
            'corner_radius': 20,
            'border_width': 1,
            'border_color': COLORS['border_light']
        }

        # Input styles
        self.input_style = {
            'fg_color': COLORS['bg_secondary'],
            'border_color': COLORS['border_light'],
            'border_width': 2,
            'corner_radius': 15,
            'text_color': COLORS['text_primary'],
            'placeholder_text_color': COLORS['text_light'],
            'font': ctk.CTkFont(size=14)
        }

    def setup_micro_interactions(self):
        """Setup micro-interactions and animations"""
        # Pulse animation for recording button
        self.pulse_animation_id = None
        self.recording_pulse = False

        # Hover effects
        self.setup_hover_effects()

        # Status animations
        self.setup_status_animations()

    def setup_hover_effects(self):
        """Setup hover effects for interactive elements"""
        pass  # Will be implemented in individual widgets

    def setup_status_animations(self):
        """Setup status animations"""
        self.status_animation_running = False
        self.status_dots = 0

    def animate_recording_button(self):
        """Animate the recording button with pulse effect"""
        if self.is_recording and not self.recording_pulse:
            self.recording_pulse = True
            self.pulse_recording_button()

    def pulse_recording_button(self):
        """Create pulse animation for recording button"""
        if self.is_recording:
            # Change button color
            current_color = self.record_button.cget('fg_color')
            if current_color == COLORS['error']:
                self.record_button.configure(fg_color='#FF6B6B')
            else:
                self.record_button.configure(fg_color=COLORS['error'])

            # Schedule next pulse
            self.root.after(500, self.pulse_recording_button)
        else:
            self.recording_pulse = False
            self.record_button.configure(fg_color=COLORS['success'])

    def animate_status_text(self, message):
        """Animate status text with loading dots"""
        if not self.status_animation_running:
            self.status_animation_running = True
            self.status_dots = 0
            self.update_status_dots(message)

    def update_status_dots(self, base_message):
        """Update status dots animation"""
        if self.status_animation_running:
            dots = '.' * (self.status_dots % 4)
            self.status_label.configure(text=f"{base_message}{dots}")
            self.status_dots += 1
            self.root.after(300, lambda: self.update_status_dots(base_message))

    def stop_status_animation(self):
        """Stop status animation"""
        self.status_animation_running = False

    def create_widgets(self):
        """Create all GUI widgets with neumorphism/liquid glass theme"""
        # Main container with neumorphism styling
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=COLORS['bg_primary'],
            corner_radius=0
        )

        # Header section with glass effect
        self.header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS['bg_secondary'],
            corner_radius=30,
            height=80
        )

        # Title with modern typography
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎤 Troice",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['text_primary']
        )

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Real-time speech recognition with intelligent speaker detection",
            font=ctk.CTkFont(size=16),
            text_color=COLORS['text_secondary']
        )

        # Main content area with tabs
        self.notebook = ctk.CTkTabview(
            self.main_frame,
            fg_color=COLORS['bg_secondary'],
            segmented_button_fg_color=COLORS['bg_tertiary'],
            segmented_button_selected_color=COLORS['accent_primary'],
            segmented_button_selected_hover_color='#2563EB',
            text_color=COLORS['text_primary'],
            corner_radius=25
        )

        # Create tabs with enhanced design
        self.create_transcription_tab()
        self.create_speaker_detection_tab()
        self.create_speaker_management_tab()
        self.create_settings_tab()

        # Enhanced status bar with glass effect
        self.status_frame = ctk.CTkFrame(
            self.root,
            fg_color=COLORS['bg_secondary'],
            corner_radius=25,
            height=80
        )

        # Status label with animation support
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="✨ Ready to transcribe",
            font=ctk.CTkFont(size=16, weight="normal"),
            text_color=COLORS['text_primary']
        )

        # Progress bar with neumorphism styling
        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            fg_color=COLORS['bg_tertiary'],
            progress_color=COLORS['accent_success'],
            corner_radius=15,
            height=25
        )
        self.progress_bar.set(0)

        # Live transcription indicator
        self.live_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color=COLORS['accent_success']
        )

    def create_transcription_tab(self):
        """Create transcription tab with soft milk theme"""
        self.transcription_tab = self.notebook.add("🎤 Transcription")

        # File selection section with card-like design
        file_card = ctk.CTkFrame(
            self.transcription_tab,
            fg_color=COLORS['secondary'],
            corner_radius=15,
            border_width=1,
            border_color=COLORS['border']
        )
        file_card.pack(fill="x", padx=20, pady=(20, 10))

        # Section title with icon
        section_title = ctk.CTkLabel(
            file_card,
            text="📁 Audio File Selection",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        )
        section_title.pack(anchor="w", padx=20, pady=(15, 5))

        # File input with modern styling
        file_input_frame = ctk.CTkFrame(file_card, fg_color="transparent")
        file_input_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.file_path_var = tk.StringVar()
        self.file_entry = ctk.CTkEntry(
            file_input_frame,
            textvariable=self.file_path_var,
            placeholder_text="Choose an audio file or drag & drop here...",
            height=45,
            fg_color='white',
            border_color=COLORS['border'],
            border_width=1,
            corner_radius=8,
            text_color=COLORS['text'],
            placeholder_text_color=COLORS['text_light'],
            font=ctk.CTkFont(size=13)
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_button = ctk.CTkButton(
            file_input_frame,
            text="📂 Browse",
            width=120,
            height=45,
            command=self.browse_file,
            fg_color=COLORS['success'],
            hover_color='#90EE90',
            text_color=COLORS['text'],
            corner_radius=15,
            border_width=0,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.browse_button.pack(side="right")

        # Action buttons section
        actions_card = ctk.CTkFrame(
            self.transcription_tab,
            fg_color=COLORS['secondary'],
            corner_radius=15,
            border_width=1,
            border_color=COLORS['border']
        )
        actions_card.pack(fill="x", padx=20, pady=10)

        actions_title = ctk.CTkLabel(
            actions_card,
            text="⚡ Quick Actions",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        )
        actions_title.pack(anchor="w", padx=20, pady=(15, 10))

        # Button grid layout - all buttons on same row
        button_grid = ctk.CTkFrame(actions_card, fg_color="transparent")
        button_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Single row for all buttons with consistent styling
        button_row = ctk.CTkFrame(button_grid, fg_color="transparent")
        button_row.pack(fill="x")

        # Standardized button configuration for consistency
        button_config = {
            "height": 50,
            "corner_radius": 15,
            "border_width": 0,
            "font": ctk.CTkFont(size=16, weight="bold"),
            "text_color": COLORS['text']
        }

        self.transcribe_file_button = ctk.CTkButton(
            button_row,
            text="🎯 Transcribe File(s)",
            command=self.transcribe_file,
            fg_color=COLORS['success'],
            hover_color='#90EE90',
            **button_config
        )
        self.transcribe_file_button.pack(side="left", padx=(0, 10))

        self.add_file_button = ctk.CTkButton(
            button_row,
            text="➕ Add Another File",
            command=self.add_another_file,
            fg_color=COLORS['accent_secondary'],
            hover_color='#A855F7',
            **button_config
        )
        self.add_file_button.pack(side="left", padx=(0, 10))

        self.clear_button = ctk.CTkButton(
            button_row,
            text="🗑️ Clear Results",
            command=self.clear_results,
            fg_color=COLORS['warning'],
            hover_color='#FFD700',
            **button_config
        )
        self.clear_button.pack(side="left", padx=(0, 10))

        self.export_results_button = ctk.CTkButton(
            button_row,
            text="💾 Export Results",
            command=self.export_results,
            fg_color=COLORS['accent'],
            hover_color=COLORS['hover'],
            **button_config
        )
        self.export_results_button.pack(side="left")
        self.export_results_button.configure(state="disabled")

        # Results section with modern card design
        results_card = ctk.CTkFrame(
            self.transcription_tab,
            fg_color=COLORS['secondary'],
            corner_radius=15,
            border_width=1,
            border_color=COLORS['border']
        )
        results_card.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        results_title = ctk.CTkLabel(
            results_card,
            text="📝 Transcription Results",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        )
        results_title.pack(anchor="w", padx=20, pady=(15, 10))

        # Results text area with custom styling
        self.results_text = scrolledtext.ScrolledText(
            results_card,
            height=15,
            wrap=tk.WORD,
            font=('Segoe UI', 12),
            bg='white',
            fg=COLORS['text'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=15
        )
        self.results_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Add placeholder text
        self.results_text.insert(
            tk.END, "✨ Your transcription results will appear here...\n\n")
        self.results_text.insert(tk.END, "💡 Tips:\n")
        self.results_text.insert(
            tk.END, "• Use clear audio files for best results\n")
        self.results_text.insert(
            tk.END, "• Try different recognition engines if needed\n")
        self.results_text.insert(
            tk.END, "• Export results in your preferred format\n")

    def create_speaker_detection_tab(self):
        """Create speaker detection tab"""
        self.speaker_tab = self.notebook.add("Speaker Detection")

        # File selection for speaker detection
        file_frame = ctk.CTkFrame(self.speaker_tab)
        file_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(file_frame, text="Audio File for Speaker Detection:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        file_select_frame = ctk.CTkFrame(file_frame)
        file_select_frame.pack(fill="x", padx=5, pady=5)

        self.speaker_file_var = tk.StringVar()
        self.speaker_file_entry = ctk.CTkEntry(
            file_select_frame, textvariable=self.speaker_file_var, placeholder_text="Select audio file...")
        self.speaker_file_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5))

        self.speaker_browse_button = ctk.CTkButton(
            file_select_frame, text="Browse", command=self.browse_speaker_file)
        self.speaker_browse_button.pack(side="right")

        # Speaker detection controls
        controls_frame = ctk.CTkFrame(self.speaker_tab)
        controls_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(controls_frame, text="Speaker Detection Controls:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        button_frame = ctk.CTkFrame(controls_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        self.detect_speakers_button = ctk.CTkButton(
            button_frame, text="Detect Speakers", command=self.detect_speakers)
        self.detect_speakers_button.pack(side="left", padx=(0, 5))

        self.max_speakers_label = ctk.CTkLabel(
            button_frame, text="Max Speakers:")
        self.max_speakers_label.pack(side="left", padx=(10, 5))

        self.max_speakers_var = tk.IntVar(value=5)
        self.max_speakers_spinbox = ctk.CTkEntry(
            button_frame, textvariable=self.max_speakers_var, width=50)
        self.max_speakers_spinbox.pack(side="left", padx=(0, 5))

        # Speaker results display
        results_frame = ctk.CTkFrame(self.speaker_tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(results_frame, text="Speaker Detection Results:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        self.speaker_results_text = scrolledtext.ScrolledText(
            results_frame, height=15, wrap=tk.WORD)
        self.speaker_results_text.pack(
            fill="both", expand=True, padx=5, pady=5)

    def create_speaker_management_tab(self):
        """Create speaker management tab"""
        self.management_tab = self.notebook.add("Speaker Management")

        # Speaker profile creation
        profile_frame = ctk.CTkFrame(self.management_tab)
        profile_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(profile_frame, text="Create Speaker Profile:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        profile_controls = ctk.CTkFrame(profile_frame)
        profile_controls.pack(fill="x", padx=5, pady=5)

        self.profile_name_var = tk.StringVar()
        self.profile_name_entry = ctk.CTkEntry(
            profile_controls, textvariable=self.profile_name_var, placeholder_text="Speaker name...")
        self.profile_name_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5))

        self.profile_file_var = tk.StringVar()
        self.profile_file_entry = ctk.CTkEntry(
            profile_controls, textvariable=self.profile_file_var, placeholder_text="Audio file for profile...")
        self.profile_file_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5))

        self.profile_browse_button = ctk.CTkButton(
            profile_controls, text="Browse", command=self.browse_profile_file)
        self.profile_browse_button.pack(side="right", padx=(5, 0))

        self.create_profile_button = ctk.CTkButton(
            profile_controls, text="Create Profile", command=self.create_speaker_profile)
        self.create_profile_button.pack(side="right", padx=(5, 0))

        # Speaker identification
        identify_frame = ctk.CTkFrame(self.management_tab)
        identify_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(identify_frame, text="Identify Speaker:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        identify_controls = ctk.CTkFrame(identify_frame)
        identify_controls.pack(fill="x", padx=5, pady=5)

        self.identify_file_var = tk.StringVar()
        self.identify_file_entry = ctk.CTkEntry(
            identify_controls, textvariable=self.identify_file_var, placeholder_text="Audio file to identify...")
        self.identify_file_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5))

        self.identify_browse_button = ctk.CTkButton(
            identify_controls, text="Browse", command=self.browse_identify_file)
        self.identify_browse_button.pack(side="right", padx=(5, 0))

        self.identify_button = ctk.CTkButton(
            identify_controls, text="Identify Speaker", command=self.identify_speaker)
        self.identify_button.pack(side="right", padx=(5, 0))

        # Results display
        results_frame = ctk.CTkFrame(self.management_tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(results_frame, text="Speaker Management Results:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        self.management_results_text = scrolledtext.ScrolledText(
            results_frame, height=15, wrap=tk.WORD)
        self.management_results_text.pack(
            fill="both", expand=True, padx=5, pady=5)

    def create_settings_tab(self):
        """Create settings tab"""
        self.settings_tab = self.notebook.add("Settings")

        # Language settings
        language_frame = ctk.CTkFrame(self.settings_tab)
        language_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(language_frame, text="Language Settings:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        language_controls = ctk.CTkFrame(language_frame)
        language_controls.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(language_controls, text="Language:").pack(
            side="left", padx=(0, 5))

        self.language_var = tk.StringVar(value="en-US")
        self.language_combo = ctk.CTkComboBox(
            language_controls,
            values=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE",
                    "it-IT", "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN"],
            variable=self.language_var,
            command=self.update_language
        )
        self.language_combo.pack(side="left", padx=(0, 10))

        # Engine settings
        engine_frame = ctk.CTkFrame(self.settings_tab)
        engine_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(engine_frame, text="Recognition Engine:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        engine_controls = ctk.CTkFrame(engine_frame)
        engine_controls.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(engine_controls, text="Engine:").pack(
            side="left", padx=(0, 5))

        self.engine_var = tk.StringVar(value="google")
        self.engine_combo = ctk.CTkComboBox(
            engine_controls,
            values=["google", "sphinx"],
            variable=self.engine_var,
            command=self.update_engine
        )
        self.engine_combo.pack(side="left", padx=(0, 10))

        # Audio settings
        audio_frame = ctk.CTkFrame(self.settings_tab)
        audio_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(audio_frame, text="Audio Settings:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        audio_controls = ctk.CTkFrame(audio_frame)
        audio_controls.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(audio_controls, text="Sample Rate:").pack(
            side="left", padx=(0, 5))

        self.sample_rate_var = tk.IntVar(value=16000)
        self.sample_rate_combo = ctk.CTkComboBox(
            audio_controls,
            values=["8000", "16000", "22050", "44100", "48000"],
            variable=self.sample_rate_var,
            command=self.update_sample_rate
        )
        self.sample_rate_combo.pack(side="left", padx=(0, 10))

        # Save/Load settings
        save_frame = ctk.CTkFrame(self.settings_tab)
        save_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(save_frame, text="Settings Management:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)

        save_controls = ctk.CTkFrame(save_frame)
        save_controls.pack(fill="x", padx=5, pady=5)

        self.save_settings_button = ctk.CTkButton(
            save_controls, text="Save Settings", command=self.save_settings)
        self.save_settings_button.pack(side="left", padx=(0, 5))

        self.load_settings_button = ctk.CTkButton(
            save_controls, text="Load Settings", command=self.load_settings)
        self.load_settings_button.pack(side="left")

    def setup_layout(self):
        """Setup the main layout with neumorphism theme and top controls"""
        # Main frame fills the entire window
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Header section with recording controls
        self.header_frame.pack(fill="x", padx=20, pady=(15, 8))
        self.title_label.pack(pady=(10, 3))
        self.subtitle_label.pack(pady=(0, 5))

        # Recording controls at the top
        self.create_top_controls()

        # Main content area
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Enhanced status bar (bottom)
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Status bar layout
        status_content = ctk.CTkFrame(
            self.status_frame, fg_color="transparent")
        status_content.pack(fill="x", padx=20, pady=15)

        # Left side - status text
        self.status_label.pack(side="left")

        # Right side - progress bar
        right_side = ctk.CTkFrame(status_content, fg_color="transparent")
        right_side.pack(side="right")

        # Progress bar
        self.progress_bar.pack(side="left", padx=(
            0, 15), fill="x", expand=True)

    def create_top_controls(self):
        """Create compact recording controls with horizontal button layout"""
        # Compact top controls frame
        self.top_controls_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=COLORS['bg_secondary'],
            corner_radius=20,
            height=45,
            border_width=1,
            border_color=COLORS['border_light']
        )
        self.top_controls_frame.pack(fill="x", padx=25, pady=(0, 10))

        # Controls content with minimal spacing
        controls_content = ctk.CTkFrame(
            self.top_controls_frame, fg_color="transparent")
        controls_content.pack(fill="both", expand=True, padx=15, pady=8)

        # Left side - compact recording status
        status_frame = ctk.CTkFrame(controls_content, fg_color="transparent")
        status_frame.pack(side="left", fill="y")

        self.recording_status_label = ctk.CTkLabel(
            status_frame,
            text="🎤 Ready",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        )
        self.recording_status_label.pack(anchor="w")

        # Compact status subtitle
        self.recording_subtitle = ctk.CTkLabel(
            status_frame,
            text="Click to start",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        self.recording_subtitle.pack(anchor="w", pady=(1, 0))

        # Right side - horizontal button layout
        self.top_controls_buttons = ctk.CTkFrame(
            controls_content, fg_color="transparent")
        self.top_controls_buttons.pack(side="right", fill="y")

        # Create compact button container
        button_container = ctk.CTkFrame(
            self.top_controls_buttons,
            fg_color=COLORS['bg_tertiary'],
            corner_radius=12,
            height=40
        )
        button_container.pack(fill="y", expand=True)

        # Horizontal button layout
        button_content = ctk.CTkFrame(button_container, fg_color="transparent")
        button_content.pack(fill="both", expand=True, padx=12, pady=8)

        # Create buttons directly here with standardized size
        self.record_button = ctk.CTkButton(
            button_content,
            text="🔴",
            width=40,
            height=30,
            command=self.start_recording,
            **self.error_button_style
        )

        self.pause_button = ctk.CTkButton(
            button_content,
            text="⏸️",
            width=40,
            height=30,
            command=self.pause_recording,
            **self.neumorphism_button_style
        )

        self.stop_button = ctk.CTkButton(
            button_content,
            text="⏹️",
            width=40,
            height=30,
            command=self.stop_recording,
            **self.neumorphism_button_style
        )

        self.export_button = ctk.CTkButton(
            button_content,
            text="💾",
            width=40,
            height=30,
            command=self.export_results,
            **self.neumorphism_button_style
        )

        # Pack buttons horizontally with consistent spacing
        self.record_button.pack(side="left", padx=(0, 6))
        self.pause_button.pack(side="left", padx=(0, 6))
        self.stop_button.pack(side="left", padx=(0, 6))
        self.export_button.pack(side="left")

        # Initial button states - hide pause, disable stop and export
        self.pause_button.pack_forget()  # Hide pause button initially
        self.stop_button.configure(state="disabled")
        self.export_button.configure(state="disabled")

    def browse_file(self):
        """Browse for audio file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.current_file = file_path
            # Reset queue when a primary file is chosen
            self.file_queue = []
            # Get and display audio duration
            self.display_audio_duration(file_path)

    def add_another_file(self):
        """Add one or more extra files to a processing queue"""
        file_paths = filedialog.askopenfilenames(
            title="Add Additional Audio Files",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"),
                ("All files", "*.*")
            ]
        )
        if file_paths:
            # Initialize queue with current file if set and not already queued
            if self.current_file and self.current_file not in self.file_queue:
                self.file_queue.append(self.current_file)

            for p in file_paths:
                if p not in self.file_queue:
                    self.file_queue.append(p)

            self.update_status(f"📁 {len(self.file_queue)} file(s) queued for transcription")

    def display_audio_duration(self, file_path):
        """Display audio file duration information"""
        try:
            # Get audio info using AudioProcessor
            audio_info = self.audio_processor.get_audio_info(file_path)
            duration = audio_info['duration']

            # Format duration as MM:SS or HH:MM:SS
            if duration < 3600:  # Less than 1 hour
                duration_str = f"{int(duration // 60):02d}:{int(duration % 60):02d}"
            else:  # 1 hour or more
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Update status to show duration
            self.update_status(
                f"📁 Selected: {os.path.basename(file_path)} ({duration_str})")

        except Exception as e:
            self.update_status(f"⚠️ Could not read audio duration: {str(e)}")

    def browse_speaker_file(self):
        """Browse for speaker detection file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File for Speaker Detection",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.speaker_file_var.set(file_path)

    def browse_profile_file(self):
        """Browse for profile creation file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File for Speaker Profile",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.profile_file_var.set(file_path)

    def browse_identify_file(self):
        """Browse for speaker identification file"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File for Speaker Identification",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.identify_file_var.set(file_path)

    def transcribe_file(self):
        """Transcribe selected audio file"""
        # Build list of files to process: queue (if any) or single current file
        files_to_process = []
        if self.file_queue:
            files_to_process = self.file_queue.copy()
        elif self.file_path_var.get():
            files_to_process = [self.file_path_var.get()]

        if not files_to_process:
            messagebox.showerror("Error", "Please select an audio file first")
            return

        # For confirmation, we show info about the first file
        first_file = files_to_process[0]
        try:
            audio_info = self.audio_processor.get_audio_info(first_file)
            duration = audio_info['duration']

            # Format duration as MM:SS or HH:MM:SS
            if duration < 3600:  # Less than 1 hour
                duration_str = f"{int(duration // 60):02d}:{int(duration % 60):02d}"
            else:  # 1 hour or more
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Show confirmation dialog
            file_name = os.path.basename(first_file)
            extra = ""
            if len(files_to_process) > 1:
                extra = f"\n(+ {len(files_to_process) - 1} more file(s) in queue)"
            confirm_message = f"File: {file_name}{extra}\nDuration: {duration_str}\n\nDo you want to transcribe selected file(s)?"

            if not messagebox.askyesno("Confirm Transcription", confirm_message):
                return

        except Exception as e:
            # If we can't get duration, still show confirmation
            file_name = os.path.basename(first_file)
            extra = ""
            if len(files_to_process) > 1:
                extra = f"\n(+ {len(files_to_process) - 1} more file(s) in queue)"
            confirm_message = f"File: {file_name}{extra}\n\nDo you want to transcribe selected file(s)?"

            if not messagebox.askyesno("Confirm Transcription", confirm_message):
                return

        def transcribe_thread():
            try:
                # Clear previous results before batch
                self.root.after(0, lambda: self.results_text.delete(1.0, tk.END))

                for idx, path in enumerate(files_to_process, start=1):
                    # Get duration for large file detection
                    file_duration = None
                    try:
                        info = self.audio_processor.get_audio_info(path)
                        file_duration = info['duration']
                    except Exception:
                        pass

                    # Per-file progress callback
                    def update_progress(progress, message, file_index=idx, total=len(files_to_process)):
                        label = f"[{file_index}/{total}] {message}"
                        self.root.after(0, lambda p=progress: self.progress_bar.set(p))
                        self.root.after(0, lambda m=label: self.update_status(m))
                        if is_large_file and hasattr(self, 'loading_progress'):
                            self.root.after(
                                0, lambda p=progress, m=label: self.update_loading_progress(p, m))

                    # Live text display callback for large files
                    def display_live_text(text_chunk):
                        """Append text chunks to results in real-time"""
                        self.root.after(
                            0, lambda t=text_chunk: self.results_text.insert(tk.END, t))
                        self.root.after(0, lambda: self.results_text.see(tk.END))

                    is_large_file = file_duration is not None and file_duration > 120
                    if is_large_file:
                        self.show_loading_animation(f"Processing Large Audio File ({idx}/{len(files_to_process)})")
                        # Show header for each large file
                        header = f"\n🔴 LIVE TRANSCRIPTION ({idx}/{len(files_to_process)}): {os.path.basename(path)}\n" + "="*50 + "\n\n"
                        self.root.after(0, lambda h=header: self.results_text.insert(tk.END, h))

                    # Transcribe with progress callback and live display
                    result = self.transcriber.transcribe_audio_file(
                        path,
                        callback=update_progress if is_large_file else None,
                        live_display=display_live_text if is_large_file else None
                    )

                    # Hide loading animation
                    if is_large_file:
                        self.hide_loading_animation()

                    # For non-large files, display nicely with typing effect
                    if not is_large_file:
                        self.display_transcription_result(result)

                self.progress_bar.set(1.0)
                self.update_status("Transcription completed successfully")
                # Enable export buttons after any successful transcription
                self.root.after(0, lambda: self.export_results_button.configure(state="normal"))
                self.root.after(0, lambda: self.export_button.configure(state="normal"))

                # Auto-hide progress after 2 seconds
                self.root.after(2000, lambda: self.progress_bar.set(0))

            except Exception as e:
                self.hide_loading_animation()
                self.update_status(f"Transcription failed: {str(e)}")
                messagebox.showerror("Transcription Error", str(e))
                self.progress_bar.set(0)

        threading.Thread(target=transcribe_thread, daemon=True).start()

    def toggle_recording(self):
        """Toggle real-time recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def detect_speakers(self):
        """Detect speakers in audio file"""
        if not self.speaker_file_var.get():
            messagebox.showerror("Error", "Please select an audio file first")
            return

        def detect_thread():
            try:
                self.update_status("Detecting speakers...")
                self.progress_bar.set(0.3)

                # Load audio file
                audio_data, sr = self.audio_processor.load_audio(
                    self.speaker_file_var.get())

                self.progress_bar.set(0.5)

                # Detect speakers
                max_speakers = self.max_speakers_var.get()
                result = self.speaker_detector.detect_speakers(
                    audio_data, max_speakers)

                self.progress_bar.set(0.8)

                # Display results
                self.display_speaker_results(result)

                self.progress_bar.set(1.0)
                self.update_status("Speaker detection completed successfully")

            except Exception as e:
                self.update_status(f"Speaker detection failed: {str(e)}")
                messagebox.showerror("Speaker Detection Error", str(e))
            finally:
                self.progress_bar.set(0)

        threading.Thread(target=detect_thread, daemon=True).start()

    def create_speaker_profile(self):
        """Create speaker profile"""
        if not self.profile_name_var.get() or not self.profile_file_var.get():
            messagebox.showerror(
                "Error", "Please provide speaker name and audio file")
            return

        def create_profile_thread():
            try:
                self.update_status("Creating speaker profile...")
                self.progress_bar.set(0.3)

                # Load audio file
                audio_data, sr = self.audio_processor.load_audio(
                    self.profile_file_var.get())

                self.progress_bar.set(0.5)

                # Create profile
                profile = self.speaker_detector.create_speaker_profile(
                    audio_data, self.profile_name_var.get()
                )

                self.progress_bar.set(0.8)

                # Display results
                result_text = f"Speaker Profile Created:\n"
                result_text += f"Name: {profile['speaker_name']}\n"
                result_text += f"Created: {profile['created_at']}\n"
                result_text += f"Sample Rate: {profile['sample_rate']}\n"

                self.management_results_text.insert(
                    tk.END, result_text + "\n" + "-"*50 + "\n")

                self.progress_bar.set(1.0)
                self.update_status("Speaker profile created successfully")

            except Exception as e:
                self.update_status(f"Profile creation failed: {str(e)}")
                messagebox.showerror("Profile Creation Error", str(e))
            finally:
                self.progress_bar.set(0)

        threading.Thread(target=create_profile_thread, daemon=True).start()

    def identify_speaker(self):
        """Identify speaker from audio file"""
        if not self.identify_file_var.get():
            messagebox.showerror("Error", "Please select an audio file first")
            return

        def identify_thread():
            try:
                self.update_status("Identifying speaker...")
                self.progress_bar.set(0.3)

                # Load audio file
                audio_data, sr = self.audio_processor.load_audio(
                    self.identify_file_var.get())

                self.progress_bar.set(0.5)

                # Identify speaker
                result = self.speaker_detector.identify_speaker(audio_data)

                self.progress_bar.set(0.8)

                # Display results
                if result.get('error'):
                    result_text = f"Error: {result['error']}\n"
                else:
                    result_text = f"Speaker Identification Results:\n"
                    result_text += f"Identified Speaker: {result['identified_speaker']}\n"
                    result_text += f"Confidence: {result['confidence']:.3f}\n"
                    result_text += f"All Similarities: {result['all_similarities']}\n"

                self.management_results_text.insert(
                    tk.END, result_text + "\n" + "-"*50 + "\n")

                self.progress_bar.set(1.0)
                self.update_status("Speaker identification completed")

            except Exception as e:
                self.update_status(f"Speaker identification failed: {str(e)}")
                messagebox.showerror("Speaker Identification Error", str(e))
            finally:
                self.progress_bar.set(0)

        threading.Thread(target=identify_thread, daemon=True).start()

    def display_transcription_result(self, result):
        """Display only the transcribed text with fast typing animation"""
        # Clear ALL text when transcription starts (tips + placeholder)
        self.results_text.delete(1.0, tk.END)

        # Get only the transcribed text
        text_content = result.get('text', '')

        # Start fast typing animation for just the text
        self.type_text_only(text_content)

    def type_text_only(self, text_content):
        """Type only the transcribed text with fast animation"""
        if not text_content:
            return

        # Configure text widget for bold text
        self.results_text.tag_configure("bold", font=('Segoe UI', 12, 'bold'))

        # Start typing animation
        self.typing_index = 0
        self.typing_text = text_content
        self.current_position = "1.0"  # Start at the beginning

        self.continue_text_typing()

    def continue_text_typing(self):
        """Continue typing the text with fast animation"""
        if self.typing_index < len(self.typing_text):
            char = self.typing_text[self.typing_index]

            # Insert character at current position
            self.results_text.insert(tk.END, char)

            # Apply bold formatting to the character
            start_pos = f"1.0+{self.typing_index}c"
            end_pos = f"1.0+{self.typing_index + 1}c"
            self.results_text.tag_add("bold", start_pos, end_pos)

            # Scroll to show the new character
            self.results_text.see(tk.END)

            self.typing_index += 1
            # Much faster typing - 10ms delay
            self.root.after(10, self.continue_text_typing)

    def display_speaker_results(self, result):
        """Display speaker detection results"""
        if result.get('error'):
            result_text = f"Error: {result['error']}\n"
        else:
            result_text = f"Speaker Detection Results:\n"
            result_text += f"Total Speakers: {result['total_speakers']}\n"
            result_text += f"Processing Time: {result['processing_time']}\n\n"

            for speaker in result['speakers']:
                result_text += f"Speaker: {speaker['speaker_id']}\n"
                result_text += f"Segments: {len(speaker['segments'])}\n"
                result_text += f"Total Duration: {speaker['total_duration']:.2f}s\n"
                result_text += f"Segments:\n"

                for segment in speaker['segments']:
                    result_text += f"  - {segment['start_time']:.2f}s to {segment['end_time']:.2f}s\n"
                result_text += "\n"

        self.speaker_results_text.insert(tk.END, result_text + "-" * 50 + "\n")
        self.speaker_results_text.see(tk.END)

    def clear_results(self):
        """Clear all results"""
        self.results_text.delete(1.0, tk.END)
        self.transcriber.clear_history()
        self.update_status("Results cleared")

    def export_results(self):
        """Export transcription results"""
        if not self.transcriber.get_transcription_history():
            messagebox.showwarning(
                "Warning", "No transcription results to export")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Transcription Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("CSV files", "*.csv")
            ]
        )

        if file_path:
            try:
                format_type = file_path.split('.')[-1].lower()
                self.transcriber.export_transcriptions(file_path, format_type)
                messagebox.showinfo(
                    "Success", f"Results exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def update_language(self, language):
        """Update transcription language"""
        self.transcriber.set_language(language)
        self.update_status(f"Language changed to: {language}")

    def update_engine(self, engine):
        """Update recognition engine"""
        self.transcriber.set_engine(engine)
        self.update_status(f"Engine changed to: {engine}")

    def update_sample_rate(self, sample_rate):
        """Update sample rate"""
        self.audio_processor.sample_rate = int(sample_rate)
        self.speaker_detector.sample_rate = int(sample_rate)
        self.update_status(f"Sample rate changed to: {sample_rate}")

    def save_settings(self):
        """Save current settings"""
        settings = {
            'language': self.language_var.get(),
            'engine': self.engine_var.get(),
            'sample_rate': self.sample_rate_var.get()
        }

        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_settings(self):
        """Load saved settings"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)

                self.language_var.set(settings.get('language', 'en-US'))
                self.engine_var.set(settings.get('engine', 'google'))
                self.sample_rate_var.set(settings.get('sample_rate', 16000))

                messagebox.showinfo("Success", "Settings loaded successfully")
            else:
                messagebox.showwarning("Warning", "No settings file found")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def load_speaker_profiles(self):
        """Load speaker profiles on startup"""
        try:
            if os.path.exists('speaker_profiles.json'):
                self.speaker_detector.load_speaker_profiles(
                    'speaker_profiles.json')
                self.update_status("Speaker profiles loaded")
        except Exception as e:
            logger.warning(f"Could not load speaker profiles: {str(e)}")

    def update_status(self, message):
        """Update status label with enhanced styling"""
        self.status_label.configure(text=message)
        self.root.update_idletasks()

    def start_recording(self):
        """Start recording with proper functionality"""
        if not self.is_recording:
            # Show loading animation
            self.show_loading_animation("Starting recording...")

            def recording_thread():
                try:
                    # Calibrate microphone ONCE at the start
                    self.root.after(100, lambda: self.update_status(
                        "🎤 Calibrating microphone..."))
                    self.transcriber.calibrate_microphone(duration=1.0)

                    # Hide loading and show recording UI
                    self.root.after(200, lambda: self.hide_loading_animation())
                    
                    # Start recording
                    self.root.after(200, lambda: self.update_status(
                        "🔴 Recording - Speak now!"))
                    self.root.after(200, lambda: self.recording_status_label.configure(
                        text="🔴 Live Recording"))
                    self.root.after(200, lambda: self.recording_subtitle.configure(
                        text="Transcribing as you speak"))
                    self.root.after(300, lambda: self.record_button.configure(
                        text="🔴", state="disabled"))
                    self.root.after(300, lambda: self.pause_button.pack(
                        side="left", padx=(0, 6)))  # Show pause button
                    self.root.after(
                        300, lambda: self.pause_button.configure(state="normal"))
                    self.root.after(
                        300, lambda: self.stop_button.configure(state="normal"))

                    # Disable settings during recording
                    self.root.after(
                        300, lambda: self.disable_settings_during_recording())

                    # Start actual recording
                    self.is_recording = True
                    self.is_paused = False

                    # Setup live transcription display for recording
                    self.root.after(
                        0, lambda: self.results_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.results_text.insert(
                        tk.END, "🔴 LIVE RECORDING - Speak Now:\n" + "="*50 + "\n\n"))

                    # Start continuous recording loop
                    self.continuous_recording_active = True
                    while self.continuous_recording_active and self.is_recording:
                        try:
                            # Don't skip pause state
                            if self.is_paused:
                                time.sleep(0.5)  # Wait while paused
                                continue

                            # Record continuously - listens until natural pause in speech
                            result = self.transcriber.transcribe_realtime(
                                duration=None,  # No duration limit - continuous
                                timeout=2  # Wait up to 2 seconds for speech to start
                            )

                            # Display result LIVE if there's text
                            if result.get('text') and result['text'].strip():
                                text = result['text']
                                # Remove disfluencies for live transcription too
                                text = self.transcriber._remove_disfluencies(text)
                                # Append to live transcription immediately (0ms delay)
                                self.root.after(
                                    0, lambda t=text: self.results_text.insert(tk.END, t + " "))
                                self.root.after(
                                    0, lambda: self.results_text.see(tk.END))
                                logger.info(f"Displayed live text: {text[:30]}...")

                            # No artificial delay - keep listening immediately
                            # Loop continues immediately to start next listen cycle
                            
                        except sr.WaitTimeoutError:
                            # No speech detected - this is normal, just keep listening
                            # No delay needed - immediately continue to next listen cycle
                            continue
                        except Exception as e:
                            logger.error(f"Recording error: {str(e)}")
                            self.root.after(0, lambda e=e: self.show_notification(
                                f"Recording error: {str(e)}", "error"))
                            time.sleep(1)  # Brief pause before retrying
                            continue

                    self.root.after(0, lambda: self.show_notification(
                        "🎤 Recording completed", "success"))

                except Exception as e:
                    self.root.after(0, lambda: self.show_notification(
                        f"Recording failed: {str(e)}", "error"))
                    self.root.after(0, lambda: self.stop_recording())
                finally:
                    self.root.after(0, lambda: self.hide_loading_animation())

            threading.Thread(target=recording_thread, daemon=True).start()
        else:
            self.show_notification("⚠️ Already recording", "warning")

    def pause_recording(self):
        """Pause recording"""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.pause_button.configure(text="▶️ Resume")
            self.recording_status_label.configure(text="⏸️ Paused")
            self.recording_subtitle.configure(text="Click resume")
            self.update_status("⏸️ Recording paused")
            self.show_notification("⏸️ Recording paused", "warning")
        elif self.is_paused:
            self.is_paused = False
            self.pause_button.configure(text="⏸️ Pause")
            self.recording_status_label.configure(text="🔴 Recording")
            self.recording_subtitle.configure(text="Live transcription")
            self.update_status("🔴 Recording resumed")
            self.show_notification("▶️ Recording resumed", "success")
        else:
            self.show_notification("⚠️ Not recording", "warning")

    def stop_recording(self):
        """Stop recording completely"""
        if self.is_recording:
            # Show loading animation
            self.show_loading_animation("Stopping recording...")

            # Stop continuous recording
            self.continuous_recording_active = False
            self.is_recording = False
            self.is_paused = False

            # Update UI
            self.record_button.configure(text="🔴", state="normal")
            self.pause_button.pack_forget()  # Hide pause button
            self.stop_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.recording_status_label.configure(text="🎤 Ready")
            self.recording_subtitle.configure(text="Click to start")

            # Re-enable settings
            self.enable_settings_after_recording()

            self.update_status("⏹️ Recording stopped")
            self.show_notification("⏹️ Recording stopped", "info")
            self.hide_loading_animation()
            # Allow exporting any recorded content
            self.export_results_button.configure(state="normal")
            self.export_button.configure(state="normal")
        else:
            self.show_notification("⚠️ Not recording", "warning")

    def show_loading_animation(self, message="Loading..."):
        """Show loading animation with enhanced display"""
        self.loading_frame = ctk.CTkFrame(
            self.root,
            fg_color=COLORS['bg_secondary'],
            corner_radius=30,
            width=500,
            height=200
        )
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Main loading text
        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text=message,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text_primary']
        )
        self.loading_label.pack(pady=(20, 10))

        # Subtitle with dots
        self.loading_subtitle = ctk.CTkLabel(
            self.loading_frame,
            text="Please wait",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        self.loading_subtitle.pack(pady=(0, 20))

        # Progress indicator
        self.loading_progress = ctk.CTkProgressBar(
            self.loading_frame,
            fg_color=COLORS['bg_tertiary'],
            progress_color=COLORS['accent_primary'],
            corner_radius=15,
            height=30,
            width=400
        )
        self.loading_progress.pack(pady=(0, 20))
        self.loading_progress.set(0)

        # Loading dots animation
        self.loading_dots = 0
        self.loading_message_base = message
        self.animate_loading_dots()

    def animate_loading_dots(self):
        """Animate loading dots"""
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            dots = '.' * (self.loading_dots % 4)
            self.loading_subtitle.configure(
                text=f"{self.loading_message_base}{dots}")
            self.loading_dots += 1
            self.root.after(500, self.animate_loading_dots)

    def hide_loading_animation(self):
        """Hide loading animation"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
            self.loading_dots = 0

    def update_loading_progress(self, progress, message):
        """Update loading animation progress"""
        if hasattr(self, 'loading_progress'):
            self.loading_progress.set(progress)
        if hasattr(self, 'loading_label'):
            self.loading_label.configure(text=message)

    def disable_settings_during_recording(self):
        """Disable settings controls during recording"""
        # Disable file selection
        self.file_entry.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.transcribe_file_button.configure(state="disabled")

        # Disable other controls
        self.clear_button.configure(state="disabled")

        # Disable tab switching
        for tab_name in self.notebook._segmented_button._buttons_dict:
            self.notebook._segmented_button._buttons_dict[tab_name].configure(
                state="disabled")

    def enable_settings_after_recording(self):
        """Re-enable settings controls after recording"""
        # Re-enable file selection
        self.file_entry.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.transcribe_file_button.configure(state="normal")

        # Re-enable other controls
        self.clear_button.configure(state="normal")

        # Re-enable tab switching
        for tab_name in self.notebook._segmented_button._buttons_dict:
            self.notebook._segmented_button._buttons_dict[tab_name].configure(
                state="normal")

    def start_live_transcription(self):
        """Start live transcription"""
        self.show_notification("🎤 Live transcription started", "success")
        self.update_status("🎤 Live transcription active")

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def show_notification(self, message, type="info"):
        """Show styled notification instead of messagebox"""
        # Create notification frame
        notification = ctk.CTkFrame(
            self.root,
            fg_color=COLORS['success'] if type == "success" else
            COLORS['warning'] if type == "warning" else
            COLORS['error'] if type == "error" else COLORS['accent'],
            corner_radius=10,
            height=60
        )

        # Position notification
        notification.place(relx=0.5, rely=0.1, anchor="center")

        # Notification content
        notification_label = ctk.CTkLabel(
            notification,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        notification_label.pack(expand=True)

        # Auto-hide notification
        def hide_notification():
            notification.destroy()

        self.root.after(3000, hide_notification)

    def animate_button_click(self, button):
        """Animate button click with scale effect"""
        original_width = button.cget('width')
        original_height = button.cget('height')

        # Scale down
        button.configure(width=int(original_width * 0.95),
                         height=int(original_height * 0.95))

        # Scale back up
        self.root.after(100, lambda: button.configure(
            width=original_width, height=original_height))

    def run(self):
        """Run the GUI application"""
        self.root.mainloop()


def main():
    """Main function to run the GUI application"""
    app = VoiceTranscriberGUI()
    app.run()


if __name__ == "__main__":
    main()
