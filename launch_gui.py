#!/usr/bin/env python3
"""
Enhanced Voice Transcriber GUI Launcher
Simple launcher with soft milk theme and micro-interactions
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import subprocess


def check_dependencies():
    """Check if required dependencies are installed"""
    # (pip_name, import_name) pairs
    required_packages = [
        ('customtkinter', 'customtkinter'),
        ('SpeechRecognition', 'speech_recognition'),
        ('librosa', 'librosa'),
        ('soundfile', 'soundfile'),
        ('scikit-learn', 'sklearn'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('pydub', 'pydub'),
        ('scipy', 'scipy'),
        ('google-generativeai', 'google.generativeai'),
    ]

    missing_packages = []

    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)

    return missing_packages


def install_missing_packages(packages):
    """Install missing packages"""
    try:
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Main launcher function"""
    print("🎤 Troice - Enhanced GUI Launcher")
    print("=" * 50)

    # Check dependencies
    print("🔍 Checking dependencies...")
    missing = check_dependencies()

    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        response = input(
            "Would you like to install missing packages? (y/n): ").lower().strip()

        if response in ['y', 'yes']:
            print("📦 Installing missing packages...")
            if install_missing_packages(missing):
                print("✅ All packages installed successfully!")
            else:
                print("❌ Failed to install some packages. Please install manually.")
                print("Run: pip install -r requirements.txt")
                return
        else:
            print("❌ Cannot proceed without required packages.")
            return
    else:
        print("✅ All dependencies are installed!")

    # Launch the GUI
    print("🚀 Launching Troice...")
    try:
        from voice_transcriber_gui import VoiceTranscriberGUI
        app = VoiceTranscriberGUI()
        app.run()
    except ImportError as e:
        print(f"❌ Error importing GUI: {e}")
        print("Make sure voice_transcriber_gui.py is in the same directory.")
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")


if __name__ == "__main__":
    main()
