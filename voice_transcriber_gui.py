"""
Troice — Voice Transcriber & Speaker Detection
Premium dark-mode UI — Complete Redesign
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import os
import json
import time
import logging
import speech_recognition as sr
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from voice_transcriber import VoiceTranscriber
from speaker_detector import SpeakerDetector
from audio_processor import AudioProcessor
from ai_text_enhancer import AITextEnhancer, EnhancerConfig

# ─────────────────────────────────────────────────────────────────
#  Theme — Dark Premium Palette
# ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Backgrounds
BG        = "#0D1117"
SURFACE   = "#161B22"
SURFACE2  = "#21262D"
SURFACE3  = "#2D333B"

# Borders
BORDER    = "#30363D"
BORDER2   = "#444C56"

# Accents
ACCENT    = "#6E76FF"   # indigo-purple
ACC_H     = "#818CF8"
GREEN     = "#3FB950"
GREEN_H   = "#4ADE80"
RED       = "#F85149"
RED_H     = "#FF6B63"
ORANGE    = "#E3B341"
BLUE      = "#58A6FF"
PURPLE    = "#BC8CFF"
TEAL      = "#39D0D8"

# Text
TEXT      = "#E6EDF3"
TEXT2     = "#8B949E"
TEXT3     = "#484F58"
WHITE     = "#FFFFFF"


def _f(size, weight="normal", family="Segoe UI"):
    return ctk.CTkFont(family=family, size=size, weight=weight)


# ─────────────────────────────────────────────────────────────────
#  Reusable Components
# ─────────────────────────────────────────────────────────────────

def _divider(parent, **grid_kw):
    f = ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0)
    if grid_kw:
        f.grid(**grid_kw)
    return f


def _label(parent, text, size=13, weight="normal", color=TEXT, **pack_kw):
    lbl = ctk.CTkLabel(parent, text=text, font=_f(size, weight), text_color=color)
    if pack_kw:
        lbl.pack(**pack_kw)
    return lbl


def _card(parent, title=None, title_color=TEXT2, padx=16, pady_inner=12):
    """Rounded dark surface card with optional title."""
    outer = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER)
    if title:
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=padx, pady=(pady_inner, 4))
        ctk.CTkLabel(hdr, text=title, font=_f(12, "bold"), text_color=title_color).pack(side="left")
        _sep = ctk.CTkFrame(outer, fg_color=BORDER, height=1, corner_radius=0)
        _sep.pack(fill="x", padx=padx, pady=(0, pady_inner))
    return outer


def _icon_btn(parent, text, width, height=36, fg=SURFACE2, hover=SURFACE3,
              tc=TEXT, font_size=12, weight="bold", command=None, state="normal", cr=8):
    return ctk.CTkButton(
        parent, text=text, width=width, height=height,
        corner_radius=cr, fg_color=fg, hover_color=hover,
        text_color=tc, font=_f(font_size, weight),
        command=command, state=state
    )


# ─────────────────────────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────────────────────────

class VoiceTranscriberGUI(ctk.CTk):

    # ── Init ──────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()

        self.title("Troice — Voice Transcriber")
        self.geometry("1420x880")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        # Backend
        self.transcriber      = VoiceTranscriber()
        self.speaker_detector = SpeakerDetector()
        self.audio_processor  = AudioProcessor()

        # State
        self.is_recording         = False
        self.is_paused            = False
        self.cont_rec_active      = False
        self.current_file         = None
        self.file_queue           = []
        self._rec_start_time      = None
        self._timer_id            = None
        self._pulse_id            = None
        self._pulse_state         = False
        self._active_page         = "transcribe"
        self._toast_widget        = None
        self._toast_after_id      = None

        # StringVars
        self.file_path_var    = tk.StringVar()
        self.language_var     = tk.StringVar(value="en-US")
        self.engine_var       = tk.StringVar(value="google")
        self.sample_rate_var  = tk.StringVar(value="16000")
        self.speaker_file_var = tk.StringVar()
        self.profile_name_var = tk.StringVar()
        self.profile_file_var = tk.StringVar()
        self.identify_file_var= tk.StringVar()
        self.max_speakers_var = tk.StringVar(value="5")
        # AI enhancement (Gemini BYOK)
        self.ai_model_var     = tk.StringVar(value="")
        self.ai_api_key_var   = tk.StringVar()

        # Build
        self._build_ui()
        self._load_speaker_profiles()
        self._load_settings_silent()

    # ── UI Construction ───────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_statusbar()

    # ── Sidebar ───────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, width=226)
        sb.grid(row=0, column=0, sticky="ns")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(5, weight=1)
        sb.grid_columnconfigure(0, weight=1)
        self.sidebar = sb

        # ─ Brand ──────────────────────────────────────────────
        brand = ctk.CTkFrame(sb, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 22))

        icon_lbl = ctk.CTkLabel(brand, text="🎤", font=_f(34))
        icon_lbl.pack(side="left", padx=(0, 12))

        name_box = ctk.CTkFrame(brand, fg_color="transparent")
        name_box.pack(side="left")
        ctk.CTkLabel(name_box, text="Troice",
                     font=_f(22, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(name_box, text="Voice Transcriber",
                     font=_f(11), text_color=TEXT3).pack(anchor="w")

        # ─ Divider ─────────────────────────────────────────────
        ctk.CTkFrame(sb, fg_color=BORDER, height=1, corner_radius=0).grid(
            row=1, column=0, sticky="ew", padx=0)

        # ─ Nav label ──────────────────────────────────────────
        ctk.CTkLabel(sb, text="MENU", font=_f(10, "bold"), text_color=TEXT3).grid(
            row=2, column=0, sticky="w", padx=24, pady=(18, 6))

        # ─ Nav buttons ────────────────────────────────────────
        nav_frame = ctk.CTkFrame(sb, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew", padx=12)

        self._nav_buttons = {}
        nav_items = [
            ("🎤", "Transcribe", "transcribe"),
            ("👥", "Speakers",   "speakers"),
            ("⚙️", "Settings",   "settings"),
        ]
        for icon, label, key in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"{icon}  {label}",
                anchor="w",
                height=46,
                corner_radius=10,
                fg_color=ACCENT if key == "transcribe" else "transparent",
                hover_color=SURFACE2,
                text_color=TEXT,
                font=_f(14, "bold"),
                command=lambda k=key: self._nav_switch(k)
            )
            btn.pack(fill="x", pady=3)
            self._nav_buttons[key] = btn

        # ─ Divider ─────────────────────────────────────────────
        ctk.CTkFrame(sb, fg_color=BORDER, height=1, corner_radius=0).grid(
            row=4, column=0, sticky="ew", padx=0, pady=(12, 0))

        # ─ Footer ─────────────────────────────────────────────
        footer = ctk.CTkFrame(sb, fg_color="transparent")
        footer.grid(row=6, column=0, sticky="sew", padx=20, pady=20)
        ctk.CTkLabel(footer, text="v2.0 · Premium Edition",
                     font=_f(10), text_color=TEXT3).pack(anchor="w")
        ctk.CTkLabel(footer, text="Dark Theme",
                     font=_f(10), text_color=TEXT3).pack(anchor="w")

    # ── Navigation switch ─────────────────────────────────────────

    def _nav_switch(self, key: str):
        self._active_page = key
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=ACCENT if k == key else "transparent")
        for k, page in self.pages.items():
            if k == key:
                page.grid()
            else:
                page.grid_remove()

    # ── Main container ────────────────────────────────────────────

    def _build_main(self):
        self.main_area = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self._build_transcribe_page()
        self._build_speakers_page()
        self._build_settings_page()
        self._nav_switch("transcribe")

    # ── Status bar ────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=46)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)
        self.statusbar = bar

        # Dot
        self._status_dot = ctk.CTkLabel(bar, text="●", font=_f(12), text_color=GREEN)
        self._status_dot.grid(row=0, column=0, padx=(16, 6), pady=13)

        # Message
        self._status_text = ctk.CTkLabel(bar, text="Ready to transcribe",
                                          font=_f(12), text_color=TEXT2, anchor="w")
        self._status_text.grid(row=0, column=1, sticky="w")

        # Progress
        self._progress_bar = ctk.CTkProgressBar(bar, height=4, width=180,
                                                  corner_radius=2,
                                                  fg_color=SURFACE2,
                                                  progress_color=ACCENT)
        self._progress_bar.set(0)
        self._progress_bar.grid(row=0, column=2, padx=16, pady=14)
        self._progress_bar.grid_remove()

        # Recording timer (right side)
        self._rec_timer_var = tk.StringVar(value="")
        self._rec_timer_disp = ctk.CTkLabel(bar, textvariable=self._rec_timer_var,
                                             font=_f(13, family="Consolas"),
                                             text_color=RED)
        self._rec_timer_disp.grid(row=0, column=3, padx=(0, 16), pady=13)

    # ─────────────────────────────────────────────────────────────
    #  PAGE: Transcribe
    # ─────────────────────────────────────────────────────────────

    def _build_transcribe_page(self):
        page = ctk.CTkFrame(self.main_area, fg_color=BG, corner_radius=0)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0)
        page.grid_rowconfigure(1, weight=1)
        self.pages["transcribe"] = page

        # ── Top header bar ────────────────────────────────────
        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=28, pady=(24, 16))
        hdr.grid_columnconfigure(0, weight=0)
        hdr.grid_columnconfigure(1, weight=1)

        # Left: Page title
        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text="Transcribe",
                     font=_f(24, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(title_box, text="  / Convert audio to text",
                     font=_f(13), text_color=TEXT3).pack(side="left", pady=(4, 0))

        # Right: Recording controls
        rec_box = ctk.CTkFrame(hdr, fg_color=SURFACE, corner_radius=10,
                               border_width=1, border_color=BORDER)
        rec_box.grid(row=0, column=1, sticky="e")

        rec_inner = ctk.CTkFrame(rec_box, fg_color="transparent")
        rec_inner.pack(padx=14, pady=10)

        # Recording dot + status
        self._rec_dot = ctk.CTkLabel(rec_inner, text="●", font=_f(13), text_color=TEXT3)
        self._rec_dot.pack(side="left", padx=(0, 6))
        self._rec_status_lbl = ctk.CTkLabel(rec_inner, text="Microphone ready",
                                             font=_f(12), text_color=TEXT2)
        self._rec_status_lbl.pack(side="left", padx=(0, 18))

        # Record button
        self.btn_record = ctk.CTkButton(
            rec_inner, text="⏺  Record", width=108, height=34, corner_radius=8,
            fg_color=RED, hover_color=RED_H, text_color=WHITE,
            font=_f(13, "bold"), command=self.start_recording
        )
        self.btn_record.pack(side="left", padx=(0, 8))

        # Pause button
        self.btn_pause = _icon_btn(
            rec_inner, "⏸  Pause", 96, height=34,
            command=self.pause_recording, state="disabled"
        )
        self.btn_pause.pack(side="left", padx=(0, 8))

        # Stop button
        self.btn_stop = _icon_btn(
            rec_inner, "⏹  Stop", 88, height=34,
            command=self.stop_recording, state="disabled"
        )
        self.btn_stop.pack(side="left")

        # ── Two-column body ───────────────────────────────────
        # Left: controls
        left = ctk.CTkScrollableFrame(page, fg_color=BG, corner_radius=0,
                                       scrollbar_button_color=SURFACE2,
                                       scrollbar_button_hover_color=SURFACE3)
        left.grid(row=1, column=0, sticky="nsew", padx=(28, 12), pady=(0, 20))
        left.grid_columnconfigure(0, weight=1)

        # ─ File Input Card ──────────────────────────────────
        file_card = _card(left, "📁  AUDIO FILE", title_color=TEXT2)
        file_card.pack(fill="x", pady=(0, 14))

        # File entry row
        file_row = ctk.CTkFrame(file_card, fg_color="transparent")
        file_row.pack(fill="x", padx=16, pady=(4, 12))

        self.file_entry = ctk.CTkEntry(
            file_row, textvariable=self.file_path_var,
            placeholder_text="Choose an audio file…",
            height=40, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3,
            font=_f(13)
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_browse = ctk.CTkButton(
            file_row, text="Browse", width=88, height=40, corner_radius=8,
            fg_color=SURFACE2, hover_color=SURFACE3, text_color=TEXT,
            font=_f(13, "bold"), command=self.browse_file
        )
        self.btn_browse.pack(side="right")

        # Options row
        opt_row = ctk.CTkFrame(file_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=16, pady=(0, 12))

        # Language
        lang_grp = ctk.CTkFrame(opt_row, fg_color="transparent")
        lang_grp.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(lang_grp, text="Language", font=_f(11), text_color=TEXT2).pack(anchor="w")
        self.lang_combo = ctk.CTkComboBox(
            lang_grp,
            values=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE",
                    "it-IT", "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN"],
            variable=self.language_var,
            width=148, height=36, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13), command=self.update_language
        )
        self.lang_combo.pack()

        # Engine
        eng_grp = ctk.CTkFrame(opt_row, fg_color="transparent")
        eng_grp.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(eng_grp, text="Engine", font=_f(11), text_color=TEXT2).pack(anchor="w")
        self.engine_combo = ctk.CTkComboBox(
            eng_grp,
            values=["google", "sphinx"],
            variable=self.engine_var,
            width=128, height=36, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13), command=self.update_engine
        )
        self.engine_combo.pack()

        # Action buttons
        act_row = ctk.CTkFrame(file_card, fg_color="transparent")
        act_row.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_transcribe = ctk.CTkButton(
            act_row, text="⚡  Transcribe File",
            height=42, corner_radius=8,
            fg_color=ACCENT, hover_color=ACC_H,
            text_color=WHITE, font=_f(14, "bold"),
            command=self.transcribe_file
        )
        self.btn_transcribe.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_add_file = _icon_btn(
            act_row, "➕ Queue", 90, height=42,
            command=self.add_another_file
        )
        self.btn_add_file.pack(side="left")

        # File info label
        self._file_info_lbl = ctk.CTkLabel(
            file_card, text="", font=_f(11), text_color=TEXT2
        )
        self._file_info_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # ─ Quick Tips Card ──────────────────────────────────
        tips_card = _card(left, "💡  TIPS", title_color=TEXT3)
        tips_card.pack(fill="x", pady=(0, 14))

        tips = [
            ("🎤", "Use clear, noise-free audio for best accuracy"),
            ("📁", "Supports WAV, MP3, M4A, FLAC, OGG, AAC"),
            ("🌐", "Google engine requires internet connection"),
            ("⚡", "Large files are auto-chunked for reliability"),
        ]
        tips_inner = ctk.CTkFrame(tips_card, fg_color="transparent")
        tips_inner.pack(fill="x", padx=16, pady=(0, 14))
        for icon, tip in tips:
            row = ctk.CTkFrame(tips_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=icon, font=_f(13), width=24).pack(side="left")
            ctk.CTkLabel(row, text=tip, font=_f(12), text_color=TEXT2,
                         wraplength=300, justify="left").pack(side="left", padx=(6, 0))

        # ── Right column: Output ──────────────────────────────
        right = ctk.CTkFrame(page, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 28), pady=(0, 20))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Set min width for right column
        right.configure(width=620)
        page.grid_columnconfigure(1, minsize=580)

        # Output header
        out_hdr = ctk.CTkFrame(right, fg_color="transparent")
        out_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(out_hdr, text="Output", font=_f(15, "bold"),
                     text_color=TEXT).pack(side="left")

        out_btn_frame = ctk.CTkFrame(out_hdr, fg_color="transparent")
        out_btn_frame.pack(side="right")

        self.btn_copy = _icon_btn(
            out_btn_frame, "⎘ Copy", 70, height=30, font_size=11,
            command=self._copy_results
        )
        self.btn_copy.pack(side="left", padx=(0, 6))

        self.btn_clear_out = _icon_btn(
            out_btn_frame, "✕ Clear", 66, height=30, font_size=11,
            command=self.clear_results
        )
        self.btn_clear_out.pack(side="left", padx=(0, 6))

        # AI enhancement button (Gemini)
        self.btn_ai_enhance = ctk.CTkButton(
            out_btn_frame, text="✨ Enhance with AI", width=130, height=30,
            corner_radius=6, fg_color=PURPLE, hover_color="#C9A8FF",
            text_color=WHITE, font=_f(11, "bold"),
            command=self.enhance_output_with_ai,
        )
        self.btn_ai_enhance.pack(side="left", padx=(0, 6))

        self.btn_export = ctk.CTkButton(
            out_btn_frame, text="↓ Export", width=74, height=30,
            corner_radius=6, fg_color=ACCENT, hover_color=ACC_H,
            text_color=WHITE, font=_f(11, "bold"), state="disabled",
            command=self.export_results
        )
        self.btn_export.pack(side="left")

        # Output textbox
        self.results_box = ctk.CTkTextbox(
            right,
            font=_f(13, family="Segoe UI"),
            fg_color=SURFACE,
            border_color=BORDER, border_width=1,
            corner_radius=12,
            text_color=TEXT,
            wrap="word",
            scrollbar_button_color=SURFACE2,
            scrollbar_button_hover_color=SURFACE3,
            activate_scrollbars=True
        )
        self.results_box.grid(row=1, column=0, sticky="nsew")
        self._set_output_placeholder()

        # Stats bar
        stats = ctk.CTkFrame(right, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self._words_lbl = ctk.CTkLabel(stats, text="0 words",
                                        font=_f(11), text_color=TEXT3)
        self._words_lbl.pack(side="left")
        ctk.CTkLabel(stats, text=" · ", font=_f(11), text_color=TEXT3).pack(side="left")
        self._chars_lbl = ctk.CTkLabel(stats, text="0 characters",
                                        font=_f(11), text_color=TEXT3)
        self._chars_lbl.pack(side="left")

    # ─────────────────────────────────────────────────────────────
    #  PAGE: Speakers
    # ─────────────────────────────────────────────────────────────

    def _build_speakers_page(self):
        page = ctk.CTkScrollableFrame(self.main_area, fg_color=BG, corner_radius=0,
                                       scrollbar_button_color=SURFACE2)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_remove()
        self.pages["speakers"] = page

        # Page header
        pg_hdr = ctk.CTkFrame(page, fg_color="transparent")
        pg_hdr.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 16))
        ctk.CTkLabel(pg_hdr, text="Speakers", font=_f(24, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(pg_hdr, text="  / Detect & manage speaker profiles",
                     font=_f(13), text_color=TEXT3).pack(side="left", pady=(4, 0))

        # Body grid
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="ew", padx=28)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # ─ Detect Speakers ──────────────────────────────────
        detect_card = _card(body, "🔍  DETECT SPEAKERS", title_color=BLUE)
        detect_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 14))

        dc_inner = ctk.CTkFrame(detect_card, fg_color="transparent")
        dc_inner.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(dc_inner, text="Audio file", font=_f(11), text_color=TEXT2).pack(anchor="w")
        sp_file_row = ctk.CTkFrame(dc_inner, fg_color="transparent")
        sp_file_row.pack(fill="x", pady=(4, 10))

        self.speaker_file_entry = ctk.CTkEntry(
            sp_file_row, textvariable=self.speaker_file_var,
            placeholder_text="Select audio file…",
            height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3, font=_f(13)
        )
        self.speaker_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        _icon_btn(sp_file_row, "Browse", 80, height=38,
                  command=self.browse_speaker_file).pack(side="right")

        # Max speakers
        ms_row = ctk.CTkFrame(dc_inner, fg_color="transparent")
        ms_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(ms_row, text="Max speakers:", font=_f(12), text_color=TEXT2).pack(side="left")
        self.max_speakers_entry = ctk.CTkEntry(
            ms_row, textvariable=self.max_speakers_var,
            width=60, height=34, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, font=_f(13)
        )
        self.max_speakers_entry.pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            dc_inner, text="🔍  Detect Speakers",
            height=40, corner_radius=8,
            fg_color=BLUE, hover_color="#4A94FF",
            text_color=WHITE, font=_f(13, "bold"),
            command=self.detect_speakers
        ).pack(fill="x", pady=(4, 0))

        # Speaker detection output
        ctk.CTkLabel(dc_inner, text="Results", font=_f(11), text_color=TEXT2).pack(
            anchor="w", pady=(14, 4))
        self.speaker_results_box = ctk.CTkTextbox(
            detect_card, height=200, font=_f(12, family="Consolas"),
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            corner_radius=8, text_color=TEXT, wrap="word",
            scrollbar_button_color=SURFACE2
        )
        self.speaker_results_box.pack(fill="x", padx=16, pady=(0, 16))
        self.speaker_results_box.insert("end", "Speaker detection results will appear here…")
        self.speaker_results_box.configure(state="disabled")

        # ─ Create Profile ───────────────────────────────────
        profile_card = _card(body, "👤  CREATE SPEAKER PROFILE", title_color=GREEN)
        profile_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 14))

        pc_inner = ctk.CTkFrame(profile_card, fg_color="transparent")
        pc_inner.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(pc_inner, text="Speaker name", font=_f(11), text_color=TEXT2).pack(anchor="w")
        self.profile_name_entry = ctk.CTkEntry(
            pc_inner, textvariable=self.profile_name_var,
            placeholder_text="e.g. John Doe",
            height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3, font=_f(13)
        )
        self.profile_name_entry.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(pc_inner, text="Audio sample", font=_f(11), text_color=TEXT2).pack(anchor="w")
        pf_row = ctk.CTkFrame(pc_inner, fg_color="transparent")
        pf_row.pack(fill="x", pady=(4, 10))
        self.profile_file_entry = ctk.CTkEntry(
            pf_row, textvariable=self.profile_file_var,
            placeholder_text="Select audio file…",
            height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3, font=_f(13)
        )
        self.profile_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        _icon_btn(pf_row, "Browse", 80, height=38,
                  command=self.browse_profile_file).pack(side="right")

        ctk.CTkButton(
            pc_inner, text="✚  Create Profile",
            height=40, corner_radius=8,
            fg_color=GREEN, hover_color=GREEN_H,
            text_color=WHITE, font=_f(13, "bold"),
            command=self.create_speaker_profile
        ).pack(fill="x", pady=(4, 0))

        # ─ Identify Speaker ─────────────────────────────────
        identify_card = _card(body, "🎯  IDENTIFY SPEAKER", title_color=PURPLE)
        identify_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        id_inner = ctk.CTkFrame(identify_card, fg_color="transparent")
        id_inner.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(id_inner, text="Audio file to identify", font=_f(11), text_color=TEXT2).pack(anchor="w")
        id_file_row = ctk.CTkFrame(id_inner, fg_color="transparent")
        id_file_row.pack(fill="x", pady=(4, 10))
        self.identify_file_entry = ctk.CTkEntry(
            id_file_row, textvariable=self.identify_file_var,
            placeholder_text="Select audio file…",
            height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3, font=_f(13)
        )
        self.identify_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        _icon_btn(id_file_row, "Browse", 80, height=38,
                  command=self.browse_identify_file).pack(side="right")

        id_btn_row = ctk.CTkFrame(id_inner, fg_color="transparent")
        id_btn_row.pack(fill="x")
        ctk.CTkButton(
            id_btn_row, text="🎯  Identify Speaker",
            height=40, width=200, corner_radius=8,
            fg_color=PURPLE, hover_color="#C9A8FF",
            text_color=WHITE, font=_f(13, "bold"),
            command=self.identify_speaker
        ).pack(side="left")

        ctk.CTkLabel(id_inner, text="Result", font=_f(11), text_color=TEXT2).pack(
            anchor="w", pady=(14, 4))
        self.management_results_box = ctk.CTkTextbox(
            identify_card, height=120, font=_f(12, family="Consolas"),
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            corner_radius=8, text_color=TEXT, wrap="word",
            scrollbar_button_color=SURFACE2
        )
        self.management_results_box.pack(fill="x", padx=16, pady=(0, 16))
        self.management_results_box.insert("end", "Speaker identification results will appear here…")
        self.management_results_box.configure(state="disabled")

    # ─────────────────────────────────────────────────────────────
    #  PAGE: Settings
    # ─────────────────────────────────────────────────────────────

    def _build_settings_page(self):
        page = ctk.CTkScrollableFrame(self.main_area, fg_color=BG, corner_radius=0,
                                       scrollbar_button_color=SURFACE2)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_remove()
        self.pages["settings"] = page

        # Page header
        pg_hdr = ctk.CTkFrame(page, fg_color="transparent")
        pg_hdr.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 16))
        ctk.CTkLabel(pg_hdr, text="Settings", font=_f(24, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(pg_hdr, text="  / Configure your preferences",
                     font=_f(13), text_color=TEXT3).pack(side="left", pady=(4, 0))

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="ew", padx=28)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # ─ Language & Engine ────────────────────────────────
        le_card = _card(body, "🌐  LANGUAGE & ENGINE", title_color=BLUE)
        le_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 14))

        le_inner = ctk.CTkFrame(le_card, fg_color="transparent")
        le_inner.pack(fill="x", padx=16, pady=(0, 16))

        # Language row
        ctk.CTkLabel(le_inner, text="Recognition language",
                     font=_f(12), text_color=TEXT2).pack(anchor="w")
        self.settings_lang_combo = ctk.CTkComboBox(
            le_inner,
            values=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE",
                    "it-IT", "pt-BR", "ru-RU", "ja-JP", "ko-KR", "zh-CN"],
            variable=self.language_var,
            width=260, height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13), command=self.update_language
        )
        self.settings_lang_combo.pack(anchor="w", pady=(4, 14))

        # Engine row
        ctk.CTkLabel(le_inner, text="Recognition engine",
                     font=_f(12), text_color=TEXT2).pack(anchor="w")
        self.settings_engine_combo = ctk.CTkComboBox(
            le_inner,
            values=["google", "sphinx"],
            variable=self.engine_var,
            width=260, height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13), command=self.update_engine
        )
        self.settings_engine_combo.pack(anchor="w", pady=(4, 0))

        # Engine note
        ctk.CTkLabel(
            le_inner,
            text="ⓘ  Google requires internet  ·  Sphinx works offline",
            font=_f(11), text_color=TEXT3, wraplength=280, justify="left"
        ).pack(anchor="w", pady=(8, 0))

        # ─ Audio Settings ───────────────────────────────────
        audio_card = _card(body, "🎛️  AUDIO SETTINGS", title_color=ORANGE)
        audio_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 14))

        ac_inner = ctk.CTkFrame(audio_card, fg_color="transparent")
        ac_inner.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(ac_inner, text="Sample rate (Hz)",
                     font=_f(12), text_color=TEXT2).pack(anchor="w")
        self.settings_sr_combo = ctk.CTkComboBox(
            ac_inner,
            values=["8000", "16000", "22050", "44100", "48000"],
            variable=self.sample_rate_var,
            width=180, height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13), command=self.update_sample_rate
        )
        self.settings_sr_combo.pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            ac_inner,
            text="ⓘ  16000 Hz recommended for speech recognition",
            font=_f(11), text_color=TEXT3
        ).pack(anchor="w", pady=(8, 0))

        # ─ AI Enhancement (Gemini 1.5 Flash, BYOK) ─────────────
        ai_card = _card(body, "✨  AI ENHANCEMENT (GEMINI)", title_color=PURPLE)
        ai_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        ai_inner = ctk.CTkFrame(ai_card, fg_color="transparent")
        ai_inner.pack(fill="x", padx=16, pady=(0, 16))

        # Model selector (required before using Troice)
        ctk.CTkLabel(
            ai_inner,
            text="AI model (required before uploading audio)",
            font=_f(12), text_color=TEXT2
        ).pack(anchor="w")
        self.ai_model_combo = ctk.CTkComboBox(
            ai_inner,
            values=["gemini-1.5-flash"],
            variable=self.ai_model_var,
            width=260, height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            button_color=SURFACE3, button_hover_color=BORDER2,
            dropdown_fg_color=SURFACE, dropdown_hover_color=SURFACE2,
            text_color=TEXT, dropdown_text_color=TEXT,
            font=_f(13),
        )
        self.ai_model_combo.pack(anchor="w", pady=(4, 10))

        # API key entry (BYOK)
        ctk.CTkLabel(
            ai_inner,
            text="Gemini API key (BYOK)",
            font=_f(12), text_color=TEXT2
        ).pack(anchor="w")
        self.ai_api_key_entry = ctk.CTkEntry(
            ai_inner,
            textvariable=self.ai_api_key_var,
            placeholder_text="Paste your Google Gemini API key…",
            height=38, corner_radius=8,
            fg_color=SURFACE2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text_color=TEXT3,
            font=_f(13),
            show="*",
        )
        self.ai_api_key_entry.pack(fill="x", pady=(4, 4))

        ctk.CTkLabel(
            ai_inner,
            text="ⓘ  Your key is used locally by Troice only. It is not stored or sent anywhere else.",
            font=_f(11), text_color=TEXT3, wraplength=520, justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # ─ Presets section ──────────────────────────────────
        preset_card = _card(body, "⚡  QUICK PRESETS", title_color=ACCENT)
        preset_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        presets_inner = ctk.CTkFrame(preset_card, fg_color="transparent")
        presets_inner.pack(fill="x", padx=16, pady=(0, 16))

        presets_desc = ctk.CTkLabel(
            presets_inner,
            text="Apply a preset configuration with one click",
            font=_f(12), text_color=TEXT2
        )
        presets_desc.pack(anchor="w", pady=(0, 12))

        preset_row = ctk.CTkFrame(presets_inner, fg_color="transparent")
        preset_row.pack(fill="x")

        presets = [
            ("🎤 Interview",   "en-US",  "google",  "16000"),
            ("📞 Phone Call",  "en-US",  "google",  "8000"),
            ("🌍 Multilingual","es-ES",  "google",  "16000"),
            ("💻 Offline",     "en-US",  "sphinx",  "16000"),
        ]
        for label, lang, eng, sr_ in presets:
            ctk.CTkButton(
                preset_row, text=label,
                height=38, corner_radius=8,
                fg_color=SURFACE2, hover_color=SURFACE3,
                text_color=TEXT, font=_f(12, "bold"),
                command=lambda l=lang, e=eng, s=sr_: self._apply_preset(l, e, s)
            ).pack(side="left", padx=(0, 10))

        # ─ Save / Load ──────────────────────────────────────
        save_card = _card(body, "💾  PROFILE MANAGEMENT", title_color=GREEN)
        save_card.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 28))

        save_inner = ctk.CTkFrame(save_card, fg_color="transparent")
        save_inner.pack(fill="x", padx=16, pady=(0, 16))

        save_row = ctk.CTkFrame(save_inner, fg_color="transparent")
        save_row.pack(fill="x")

        ctk.CTkButton(
            save_row, text="💾  Save Settings",
            width=160, height=40, corner_radius=8,
            fg_color=GREEN, hover_color=GREEN_H,
            text_color=WHITE, font=_f(13, "bold"),
            command=self.save_settings
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            save_row, text="📂  Load Settings",
            width=160, height=40, corner_radius=8,
            fg_color=SURFACE2, hover_color=SURFACE3,
            text_color=TEXT, font=_f(13, "bold"),
            command=self.load_settings
        ).pack(side="left")

    # ─────────────────────────────────────────────────────────────
    #  Output helpers
    # ─────────────────────────────────────────────────────────────

    def _set_output_placeholder(self):
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("end",
            "Your transcription will appear here.\n\n"
            "• Select a file and click ⚡ Transcribe, or\n"
            "• Click ⏺ Record to transcribe live from your microphone.\n"
        )
        self.results_box.configure(text_color=TEXT3)

    def _write_output(self, text: str, append: bool = False):
        """Write text to results box (thread-safe via after)."""
        def _do():
            self.results_box.configure(state="normal", text_color=TEXT)
            if not append:
                self.results_box.delete("1.0", "end")
            self.results_box.insert("end", text)
            self.results_box.see("end")
            self._update_stats()
        self.after(0, _do)

    def _append_output(self, text: str):
        self._write_output(text, append=True)

    def _update_stats(self):
        content = self.results_box.get("1.0", "end").strip()
        words = len(content.split()) if content else 0
        chars = len(content)
        self._words_lbl.configure(text=f"{words:,} words")
        self._chars_lbl.configure(text=f"{chars:,} characters")

    def _copy_results(self):
        text = self.results_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._show_toast("Copied to clipboard!", "green")

    # ─────────────────────────────────────────────────────────────
    #  Status helpers
    # ─────────────────────────────────────────────────────────────

    def update_status(self, message: str, color: str = TEXT2, dot_color: str = None):
        def _do():
            self._status_text.configure(text=message, text_color=color)
            if dot_color:
                self._status_dot.configure(text_color=dot_color)
            self.update_idletasks()
        self.after(0, _do)

    def _set_progress(self, value: float):
        def _do():
            if value <= 0:
                self._progress_bar.grid_remove()
            else:
                self._progress_bar.grid()
                self._progress_bar.set(min(value, 1.0))
        self.after(0, _do)

    def _show_toast(self, message: str, type_: str = "info"):
        """Show a floating toast notification."""
        color_map = {"green": GREEN, "red": RED, "orange": ORANGE,
                     "blue": BLUE, "info": ACCENT}
        bg_color = color_map.get(type_, ACCENT)

        # Destroy previous toast
        if self._toast_widget and self._toast_widget.winfo_exists():
            self._toast_widget.destroy()
        if self._toast_after_id:
            self.after_cancel(self._toast_after_id)

        toast = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=10, height=46)
        toast.place(relx=0.5, y=60, anchor="n")

        ctk.CTkLabel(
            toast, text=message, font=_f(13, "bold"),
            text_color=WHITE, padx=20, pady=10
        ).pack()

        self._toast_widget = toast
        self._toast_after_id = self.after(2800, lambda: toast.destroy() if toast.winfo_exists() else None)

    # ─────────────────────────────────────────────────────────────
    #  Recording timer
    # ─────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._rec_start_time = time.time()
        self._tick_timer()

    def _tick_timer(self):
        if self.is_recording and not self.is_paused:
            elapsed = int(time.time() - self._rec_start_time)
            mins, secs = divmod(elapsed, 60)
            self._rec_timer_var.set(f"⏺  {mins:02d}:{secs:02d}")
        elif self.is_paused:
            pass  # freeze timer display
        else:
            self._rec_timer_var.set("")
            return
        self._timer_id = self.after(1000, self._tick_timer)

    def _stop_timer(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._rec_timer_var.set("")

    def _start_pulse(self):
        """Pulse the recording dot."""
        self._pulse_state = not self._pulse_state
        if self.is_recording and not self.is_paused:
            self._rec_dot.configure(text_color=RED if self._pulse_state else SURFACE3)
            self._pulse_id = self.after(600, self._start_pulse)
        else:
            if self.is_paused:
                self._rec_dot.configure(text_color=ORANGE)
            else:
                self._rec_dot.configure(text_color=TEXT3)

    def _stop_pulse(self):
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
            self._pulse_id = None
        self._rec_dot.configure(text_color=TEXT3)

    # ─────────────────────────────────────────────────────────────
    #  Recording logic
    # ─────────────────────────────────────────────────────────────

    def start_recording(self):
        if self.is_recording:
            self._show_toast("Already recording", "orange")
            return

        if not self._ensure_ai_configured():
            return

        self.btn_record.configure(state="disabled")
        self.btn_pause.configure(state="normal")
        self.btn_stop.configure(state="normal")
        self._rec_status_lbl.configure(text="Calibrating…", text_color=ORANGE)
        update_status = self.update_status
        update_status("Calibrating microphone…", ORANGE, ORANGE)

        def _thread():
            try:
                self.transcriber.calibrate_microphone(duration=1.0)

                self.after(0, lambda: self._rec_status_lbl.configure(
                    text="● Recording", text_color=RED))
                self.after(0, lambda: self.results_box.configure(
                    state="normal", text_color=TEXT))
                self.after(0, lambda: self.results_box.delete("1.0", "end"))
                self.after(0, lambda: self.results_box.insert(
                    "end", "🔴  Live Recording…\n\n"))

                self.is_recording = True
                self.is_paused = False
                self.after(0, self._start_timer)
                self.after(0, self._start_pulse)
                self.after(0, lambda: update_status(
                    "Recording — speak now", RED, RED))

                self.cont_rec_active = True
                while self.cont_rec_active and self.is_recording:
                    if self.is_paused:
                        time.sleep(0.4)
                        continue
                    try:
                        result = self.transcriber.transcribe_realtime(
                            duration=None, timeout=2)
                        if result.get("text") and result["text"].strip():
                            text = result["text"]
                            self.after(0, lambda t=text: (
                                self.results_box.insert("end", t + " "),
                                self.results_box.see("end"),
                                self._update_stats()
                            ))
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Recording error: {e}")
                        time.sleep(1)

                self.after(0, lambda: self._show_toast("Recording complete", "green"))

            except Exception as e:
                self.after(0, lambda: self._show_toast(f"Error: {e}", "red"))
                self.after(0, self.stop_recording)

        threading.Thread(target=_thread, daemon=True).start()

    def pause_recording(self):
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.btn_pause.configure(text="▶  Resume")
            self._rec_status_lbl.configure(text="⏸ Paused", text_color=ORANGE)
            self._rec_dot.configure(text_color=ORANGE)
            self.update_status("Paused", ORANGE, ORANGE)
            self._show_toast("Recording paused", "orange")
        elif self.is_paused:
            self.is_paused = False
            self.btn_pause.configure(text="⏸  Pause")
            self._rec_status_lbl.configure(text="● Recording", text_color=RED)
            self.after(0, self._start_pulse)
            self.update_status("Recording — speak now", RED, RED)
            self._show_toast("Recording resumed", "green")

    def stop_recording(self):
        if not self.is_recording:
            return
        self.cont_rec_active = False
        self.is_recording = False
        self.is_paused = False

        self._stop_timer()
        self._stop_pulse()

        self.btn_record.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="⏸  Pause")
        self.btn_stop.configure(state="disabled")
        self._rec_status_lbl.configure(text="Microphone ready", text_color=TEXT2)
        self.btn_export.configure(state="normal")
        self.update_status("Recording stopped — results ready", GREEN, GREEN)
        self._show_toast("Recording stopped", "green")

    # ─────────────────────────────────────────────────────────────
    #  File transcription
    # ─────────────────────────────────────────────────────────────

    def browse_file(self):
        if not self._ensure_ai_configured():
            return
        path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("WAV files", "*.wav"), ("MP3 files", "*.mp3"),
                ("M4A files", "*.m4a"), ("All files", "*.*")
            ]
        )
        if path:
            self.file_path_var.set(path)
            self.current_file = path
            self.file_queue = []
            self._display_file_info(path)

    def _display_file_info(self, path: str):
        try:
            info = self.audio_processor.get_audio_info(path)
            dur = info["duration"]
            if dur < 3600:
                dur_str = f"{int(dur//60):02d}:{int(dur%60):02d}"
            else:
                h = int(dur//3600); m = int((dur%3600)//60); s = int(dur%60)
                dur_str = f"{h:02d}:{m:02d}:{s:02d}"
            name = os.path.basename(path)
            self._file_info_lbl.configure(
                text=f"📄  {name}  ·  {dur_str}", text_color=TEXT2)
        except Exception:
            self._file_info_lbl.configure(
                text=f"📄  {os.path.basename(path)}", text_color=TEXT2)

    def add_another_file(self):
        if not self._ensure_ai_configured():
            return
        paths = filedialog.askopenfilenames(
            title="Add Audio Files to Queue",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                ("All files", "*.*")
            ]
        )
        if paths:
            if self.current_file and self.current_file not in self.file_queue:
                self.file_queue.append(self.current_file)
            for p in paths:
                if p not in self.file_queue:
                    self.file_queue.append(p)
            self.update_status(f"📁  {len(self.file_queue)} file(s) queued", BLUE, BLUE)
            self._show_toast(f"{len(self.file_queue)} files queued", "blue")

    def transcribe_file(self):
        if not self._ensure_ai_configured():
            return
        files = self.file_queue.copy() if self.file_queue else (
            [self.file_path_var.get()] if self.file_path_var.get() else [])

        if not files or not files[0]:
            self._show_toast("Please select an audio file first", "orange")
            return

        self.btn_transcribe.configure(state="disabled", text="⏳  Processing…")
        self._set_progress(0.05)
        self.results_box.configure(state="normal", text_color=TEXT)
        self.results_box.delete("1.0", "end")
        self._update_stats()

        def _thread():
            try:
                for idx, path in enumerate(files, 1):
                    file_duration = None
                    try:
                        info = self.audio_processor.get_audio_info(path)
                        file_duration = info["duration"]
                    except Exception:
                        pass

                    is_large = file_duration is not None and file_duration > 120
                    total = len(files)

                    if is_large:
                        header = (f"\n▶  File {idx}/{total}: {os.path.basename(path)}\n"
                                  + "─" * 48 + "\n\n")
                        self._append_output(header)

                    def _progress(prog, msg, i=idx, t=total):
                        label = f"[{i}/{t}] {msg}"
                        self._set_progress(prog)
                        self.update_status(label, TEXT2)

                    def _live_text(chunk):
                        self.after(0, lambda c=chunk: (
                            self.results_box.insert("end", c),
                            self.results_box.see("end"),
                            self._update_stats()
                        ))

                    result = self.transcriber.transcribe_audio_file(
                        path,
                        callback=_progress if is_large else None,
                        live_display=_live_text if is_large else None
                    )

                    if not is_large:
                        text = result.get("text", "")
                        if total > 1:
                            header = (f"▶  File {idx}/{total}: {os.path.basename(path)}\n"
                                      + "─" * 48 + "\n")
                            self._append_output(header)
                        self._append_output(text + ("\n\n" if total > 1 else ""))

                self._set_progress(1.0)
                self.after(0, lambda: self.btn_export.configure(state="normal"))
                self.update_status("Transcription complete ✓", GREEN, GREEN)
                self.after(0, lambda: self._show_toast("Transcription complete!", "green"))
                self.after(2000, lambda: self._set_progress(0))

            except Exception as e:
                self.update_status(f"Error: {e}", RED, RED)
                self.after(0, lambda: self._show_toast(f"Failed: {e}", "red"))
                self._set_progress(0)
            finally:
                self.after(0, lambda: self.btn_transcribe.configure(
                    state="normal", text="⚡  Transcribe File"))

        threading.Thread(target=_thread, daemon=True).start()

    # ─────────────────────────────────────────────────────────────
    #  Results management
    # ─────────────────────────────────────────────────────────────

    def clear_results(self):
        self.transcriber.clear_history()
        self._set_output_placeholder()
        self._update_stats()
        self.btn_export.configure(state="disabled")
        self.update_status("Output cleared", TEXT2)

    def export_results(self):
        if not self.transcriber.get_transcription_history():
            # Try to export what's in the box
            content = self.results_box.get("1.0", "end").strip()
            if not content:
                self._show_toast("Nothing to export", "orange")
                return
            path = filedialog.asksaveasfilename(
                title="Export Transcription",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._show_toast("Exported successfully!", "green")
            return

        path = filedialog.asksaveasfilename(
            title="Export Transcription Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("CSV files", "*.csv")
            ]
        )
        if path:
            try:
                fmt = path.rsplit(".", 1)[-1].lower()
                self.transcriber.export_transcriptions(path, fmt)
                self._show_toast(f"Exported as .{fmt}!", "green")
            except Exception as e:
                self._show_toast(f"Export failed: {e}", "red")

    def display_transcription_result(self, result):
        text = result.get("text", "")
        self._write_output(text)
        self.btn_export.configure(state="normal")

    # ─────────────────────────────────────────────────────────────
    #  Speaker Detection
    # ─────────────────────────────────────────────────────────────

    def browse_speaker_file(self):
        path = filedialog.askopenfilename(title="Select Audio File for Speaker Detection",
                                          filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"), ("All files", "*.*")])
        if path:
            self.speaker_file_var.set(path)

    def browse_profile_file(self):
        path = filedialog.askopenfilename(title="Select Audio for Speaker Profile",
                                          filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"), ("All files", "*.*")])
        if path:
            self.profile_file_var.set(path)

    def browse_identify_file(self):
        path = filedialog.askopenfilename(title="Select Audio File to Identify",
                                          filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"), ("All files", "*.*")])
        if path:
            self.identify_file_var.set(path)

    def _write_speaker_results(self, text: str):
        def _do():
            self.speaker_results_box.configure(state="normal")
            self.speaker_results_box.delete("1.0", "end")
            self.speaker_results_box.insert("end", text)
            self.speaker_results_box.configure(state="disabled")
        self.after(0, _do)

    def _write_identify_results(self, text: str):
        def _do():
            self.management_results_box.configure(state="normal")
            self.management_results_box.delete("1.0", "end")
            self.management_results_box.insert("end", text)
            self.management_results_box.configure(state="disabled")
        self.after(0, _do)

    def detect_speakers(self):
        if not self.speaker_file_var.get():
            self._show_toast("Please select an audio file first", "orange")
            return

        self._set_progress(0.1)
        self.update_status("Detecting speakers…", BLUE, BLUE)

        def _thread():
            try:
                audio_data, sr_ = self.audio_processor.load_audio(self.speaker_file_var.get())
                self._set_progress(0.5)
                max_sp = int(self.max_speakers_var.get() or 5)
                result = self.speaker_detector.detect_speakers(audio_data, max_sp)
                self._set_progress(0.9)

                if result.get("error"):
                    text = f"Error: {result['error']}"
                else:
                    lines = [
                        f"Total Speakers:   {result['total_speakers']}",
                        f"Processing Time:  {result['processing_time']}",
                        ""
                    ]
                    for sp in result.get("speakers", []):
                        lines.append(f"Speaker: {sp['speaker_id']}")
                        lines.append(f"  Segments: {len(sp['segments'])}")
                        lines.append(f"  Total Duration: {sp['total_duration']:.2f}s")
                        for seg in sp["segments"]:
                            lines.append(f"    • {seg['start_time']:.2f}s → {seg['end_time']:.2f}s")
                        lines.append("")
                    text = "\n".join(lines)

                self._write_speaker_results(text)
                self._set_progress(0)
                self.update_status("Speaker detection complete ✓", GREEN, GREEN)
                self.after(0, lambda: self._show_toast("Speakers detected!", "green"))

            except Exception as e:
                self._set_progress(0)
                self.update_status(f"Speaker detection failed: {e}", RED, RED)
                self.after(0, lambda: self._show_toast(f"Error: {e}", "red"))

        threading.Thread(target=_thread, daemon=True).start()

    def create_speaker_profile(self):
        if not self.profile_name_var.get() or not self.profile_file_var.get():
            self._show_toast("Enter speaker name and select audio file", "orange")
            return

        self._set_progress(0.2)
        self.update_status("Creating speaker profile…", BLUE, BLUE)

        def _thread():
            try:
                audio_data, sr_ = self.audio_processor.load_audio(self.profile_file_var.get())
                self._set_progress(0.5)
                profile = self.speaker_detector.create_speaker_profile(
                    audio_data, self.profile_name_var.get())
                self._set_progress(0.9)

                text = (f"Profile Created Successfully\n"
                        f"────────────────────────────\n"
                        f"Name:         {profile['speaker_name']}\n"
                        f"Created at:   {profile['created_at']}\n"
                        f"Sample Rate:  {profile['sample_rate']}\n")

                self.after(0, lambda: messagebox.showinfo("Profile Created",
                    f"Speaker profile for '{profile['speaker_name']}' created!"))
                self._set_progress(0)
                self.update_status("Speaker profile created ✓", GREEN, GREEN)
                self.after(0, lambda: self._show_toast("Profile created!", "green"))

            except Exception as e:
                self._set_progress(0)
                self.update_status(f"Profile creation failed: {e}", RED, RED)
                self.after(0, lambda: self._show_toast(f"Error: {e}", "red"))

        threading.Thread(target=_thread, daemon=True).start()

    def identify_speaker(self):
        if not self.identify_file_var.get():
            self._show_toast("Please select an audio file first", "orange")
            return

        self._set_progress(0.2)
        self.update_status("Identifying speaker…", PURPLE, PURPLE)

        def _thread():
            try:
                audio_data, sr_ = self.audio_processor.load_audio(self.identify_file_var.get())
                self._set_progress(0.5)
                result = self.speaker_detector.identify_speaker(audio_data)
                self._set_progress(0.9)

                if result.get("error"):
                    text = f"Error: {result['error']}"
                else:
                    text = (f"Identification Result\n"
                            f"────────────────────────────\n"
                            f"Speaker:     {result['identified_speaker']}\n"
                            f"Confidence:  {result['confidence']:.3f}\n"
                            f"\nAll Similarities:\n{result['all_similarities']}")

                self._write_identify_results(text)
                self._set_progress(0)
                self.update_status("Speaker identified ✓", GREEN, GREEN)
                self.after(0, lambda: self._show_toast("Speaker identified!", "green"))

            except Exception as e:
                self._set_progress(0)
                self.update_status(f"Identification failed: {e}", RED, RED)
                self.after(0, lambda: self._show_toast(f"Error: {e}", "red"))

        threading.Thread(target=_thread, daemon=True).start()

    # ─────────────────────────────────────────────────────────────
    #  Settings
    # ─────────────────────────────────────────────────────────────

    def update_language(self, lang):
        self.transcriber.set_language(lang)
        self.language_var.set(lang)
        self.update_status(f"Language → {lang}", TEXT2)

    def update_engine(self, engine):
        self.transcriber.set_engine(engine)
        self.engine_var.set(engine)
        self.update_status(f"Engine → {engine}", TEXT2)

    def update_sample_rate(self, sr_val):
        try:
            rate = int(sr_val)
            self.audio_processor.sample_rate = rate
            self.speaker_detector.sample_rate = rate
            self.update_status(f"Sample rate → {rate} Hz", TEXT2)
        except ValueError:
            pass

    def _apply_preset(self, lang: str, engine: str, sr_: str):
        self.language_var.set(lang)
        self.engine_var.set(engine)
        self.sample_rate_var.set(sr_)
        self.transcriber.set_language(lang)
        self.transcriber.set_engine(engine)
        try:
            self.audio_processor.sample_rate = int(sr_)
            self.speaker_detector.sample_rate = int(sr_)
        except Exception:
            pass
        self.lang_combo.set(lang)
        self.engine_combo.set(engine)
        self.update_status(f"Preset applied: {lang} · {engine} · {sr_} Hz", ACCENT)
        self._show_toast("Preset applied!", "blue")

    def save_settings(self):
        settings = {
            "language": self.language_var.get(),
            "engine": self.engine_var.get(),
            "sample_rate": self.sample_rate_var.get(),
            "ai_model": self.ai_model_var.get(),
            # API key is BYOK; we do NOT persist it to disk for safety.
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            self._show_toast("Settings saved!", "green")
        except Exception as e:
            self._show_toast(f"Save failed: {e}", "red")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json") as f:
                    s = json.load(f)
                lang   = s.get("language", "en-US")
                engine = s.get("engine",   "google")
                sr_    = str(s.get("sample_rate", "16000"))
                # Restore AI model selection if present
                self.ai_model_var.set(s.get("ai_model", "gemini-1.5-flash"))
                try:
                    self.ai_model_combo.set(self.ai_model_var.get())
                except Exception:
                    pass
                self._apply_preset(lang, engine, sr_)
                self._show_toast("Settings loaded!", "green")
            else:
                self._show_toast("No saved settings found", "orange")
        except Exception as e:
            self._show_toast(f"Load failed: {e}", "red")

    def _load_settings_silent(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json") as f:
                    s = json.load(f)
                self.language_var.set(s.get("language", "en-US"))
                self.engine_var.set(s.get("engine", "google"))
                self.sample_rate_var.set(str(s.get("sample_rate", "16000")))
                self.ai_model_var.set(s.get("ai_model", "gemini-1.5-flash"))
                try:
                    if hasattr(self, "ai_model_combo"):
                        self.ai_model_combo.set(self.ai_model_var.get())
                except Exception:
                    pass
                self.transcriber.set_language(s.get("language", "en-US"))
                self.transcriber.set_engine(s.get("engine", "google"))
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    #  AI enhancement helpers (Gemini 1.5 Flash BYOK)
    # ─────────────────────────────────────────────────────────────

    def _ensure_ai_configured(self) -> bool:
        """Ensure an AI model and API key are set before audio is used."""
        model = (self.ai_model_var.get() or "").strip()
        key = (self.ai_api_key_var.get() or "").strip()
        if not model:
            self._show_toast("Please select an AI model before using Troice.", "orange")
            self.update_status("AI model required before uploading audio", ORANGE, ORANGE)
            return False
        if not key:
            self._show_toast("Please enter your Gemini API key (BYOK).", "orange")
            self.update_status("Gemini API key required (BYOK)", ORANGE, ORANGE)
            return False
        return True

    def enhance_output_with_ai(self):
        """Enhance the current transcription text using Gemini 1.5 Flash."""
        if not self._ensure_ai_configured():
            return

        raw = self.results_box.get("1.0", "end").strip()
        if not raw:
            self._show_toast("No text to enhance yet.", "orange")
            return

        self.btn_ai_enhance.configure(state="disabled", text="⏳ Enhancing…")
        self.update_status("Enhancing text with Gemini…", BLUE, BLUE)

        def _thread():
            try:
                cfg = EnhancerConfig(
                    provider="google",
                    model=(self.ai_model_var.get() or "gemini-1.5-flash").strip(),
                    google_api_key=(self.ai_api_key_var.get() or "").strip(),
                )
                enhancer = AITextEnhancer(cfg)
                result = enhancer.enhance(raw_text=raw, mode="enhance")
                enhanced = result.enhanced_text or raw

                self.after(0, lambda: self._write_output(enhanced, append=False))
                self.after(0, lambda: self._show_toast("AI enhancement complete!", "green"))
                self.update_status("AI enhancement complete ✓", GREEN, GREEN)
            except Exception as e:
                logger.error(f"AI enhancement error: {e}")
                self.after(0, lambda: self._show_toast(f"AI error: {e}", "red"))
                self.update_status(f"AI error: {e}", RED, RED)
            finally:
                self.after(
                    0,
                    lambda: self.btn_ai_enhance.configure(
                        state="normal", text="✨ Enhance with AI"
                    ),
                )

        threading.Thread(target=_thread, daemon=True).start()

    def _load_speaker_profiles(self):
        try:
            if os.path.exists("speaker_profiles.json"):
                self.speaker_detector.load_speaker_profiles("speaker_profiles.json")
                logger.info("Speaker profiles loaded")
        except Exception as e:
            logger.warning(f"Could not load speaker profiles: {e}")

    # ─────────────────────────────────────────────────────────────
    #  Entry point
    # ─────────────────────────────────────────────────────────────

    def run(self):
        self.mainloop()


# ─────────────────────────────────────────────────────────────────

def main():
    app = VoiceTranscriberGUI()
    app.run()


if __name__ == "__main__":
    main()
