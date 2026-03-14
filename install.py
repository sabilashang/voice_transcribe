#!/usr/bin/env python3
"""
Installation Script for Voice Transcriber with Speaker Detection
Automates the setup process and checks system requirements
"""

import os
import sys
import subprocess
import platform
import importlib.util


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(
            f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(
        f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def check_system_requirements():
    """Check system requirements"""
    print("\n💻 Checking system requirements...")

    # Check available memory (approximate)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4:
            print(
                f"⚠️  Available memory: {memory_gb:.1f}GB (4GB+ recommended)")
        else:
            print(f"✅ Available memory: {memory_gb:.1f}GB")
    except ImportError:
        print("⚠️  Could not check memory (psutil not available)")

    # Check OS
    os_name = platform.system()
    print(f"✅ Operating System: {os_name}")

    return True


def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        spec = importlib.util.find_spec(import_name)
        return spec is not None
    except ImportError:
        return False


def install_core_dependencies():
    """Install core dependencies"""
    print("\n📦 Installing core dependencies...")

    core_packages = [
        "SpeechRecognition",
        "librosa",
        "soundfile",
        "scikit-learn",
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        "pydub"
    ]

    failed_packages = []

    for package in core_packages:
        print(f"Installing {package}...", end=" ")
        if install_package(package):
            print("✅")
        else:
            print("❌")
            failed_packages.append(package)

    return failed_packages


def install_audio_dependencies():
    """Install audio-specific dependencies"""
    print("\n🎵 Installing audio dependencies...")

    # PyAudio installation varies by platform
    print("Installing PyAudio...", end=" ")

    if platform.system() == "Windows":
        # Try pipwin first
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pipwin"])
            subprocess.check_call(
                [sys.executable, "-m", "pipwin", "install", "pyaudio"])
            print("✅")
        except subprocess.CalledProcessError:
            # Fallback to regular pip
            if install_package("pyaudio"):
                print("✅")
            else:
                print("❌")
                print(
                    "⚠️  PyAudio installation failed. You may need to install it manually.")

    elif platform.system() == "Darwin":  # macOS
        try:
            # Try to install portaudio first
            subprocess.check_call(["brew", "install", "portaudio"],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # brew not available or portaudio already installed

        if install_package("pyaudio"):
            print("✅")
        else:
            print("❌")
            print("⚠️  PyAudio installation failed. Try: brew install portaudio")

    else:  # Linux
        if install_package("pyaudio"):
            print("✅")
        else:
            print("❌")
            print(
                "⚠️  PyAudio installation failed. Try: sudo apt-get install python3-pyaudio")


def install_gui_dependencies():
    """Install GUI dependencies"""
    print("\n🖥️  Installing GUI dependencies...")

    gui_packages = [
        "customtkinter",
        "tkinter-tooltip"
    ]

    for package in gui_packages:
        print(f"Installing {package}...", end=" ")
        if install_package(package):
            print("✅")
        else:
            print("❌")
            print(
                f"⚠️  {package} installation failed. GUI may not work properly.")


def install_optional_dependencies():
    """Install optional advanced dependencies"""
    print("\n🔬 Installing optional advanced dependencies...")

    optional_packages = [
        "pyannote.audio",
        "resemblyzer",
        "speechbrain",
        "transformers",
        "datasets"
    ]

    print("These packages are optional but provide advanced speaker detection features.")
    response = input("Install optional dependencies? (y/n): ").lower().strip()

    if response in ['y', 'yes']:
        for package in optional_packages:
            print(f"Installing {package}...", end=" ")
            if install_package(package):
                print("✅")
            else:
                print("❌")
                print(f"⚠️  {package} installation failed (optional)")


def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")

    test_modules = [
        ("SpeechRecognition", "speech_recognition"),
        ("librosa", "librosa"),
        ("sklearn", "sklearn"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("scipy", "scipy"),
        ("pydub", "pydub")
    ]

    failed_tests = []

    for display_name, import_name in test_modules:
        print(f"Testing {display_name}...", end=" ")
        if check_package(display_name, import_name):
            print("✅")
        else:
            print("❌")
            failed_tests.append(display_name)

    # Test PyAudio separately
    print("Testing PyAudio...", end=" ")
    try:
        import pyaudio
        print("✅")
    except ImportError:
        print("❌")
        failed_tests.append("PyAudio")

    # Test GUI components
    print("Testing CustomTkinter...", end=" ")
    try:
        import customtkinter
        print("✅")
    except ImportError:
        print("❌")
        failed_tests.append("CustomTkinter")

    return failed_tests


def create_sample_config():
    """Create sample configuration files"""
    print("\n⚙️  Creating configuration files...")

    # Create settings.json
    settings = {
        "language": "en-US",
        "engine": "google",
        "sample_rate": 16000,
        "max_speakers": 5,
        "chunk_duration": 30.0
    }

    try:
        import json
        with open("settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        print("✅ Created settings.json")
    except Exception as e:
        print(f"❌ Failed to create settings.json: {e}")


def main():
    """Main installation process"""
    print("=" * 60)
    print("VOICE TRANSCRIBER WITH SPEAKER DETECTION - INSTALLER")
    print("=" * 60)
    print()

    # Check Python version
    if not check_python_version():
        print("\n❌ Installation failed: Incompatible Python version")
        return False

    # Check system requirements
    if not check_system_requirements():
        print("\n⚠️  System requirements not met, but continuing...")

    # Install dependencies
    failed_core = install_core_dependencies()
    install_audio_dependencies()
    install_gui_dependencies()

    # Optional dependencies
    install_optional_dependencies()

    # Test installation
    failed_tests = test_installation()

    # Create config files
    create_sample_config()

    # Summary
    print("\n" + "=" * 60)
    print("INSTALLATION SUMMARY")
    print("=" * 60)

    if failed_core:
        print(f"❌ Failed core packages: {', '.join(failed_core)}")

    if failed_tests:
        print(f"⚠️  Failed tests: {', '.join(failed_tests)}")

    if not failed_core and not failed_tests:
        print("✅ Installation completed successfully!")
        print("\n🚀 You can now run:")
        print("   python voice_transcriber_gui.py    # GUI application")
        print("   python demo.py                     # Demo script")
    else:
        print("⚠️  Installation completed with warnings")
        print("Some features may not work properly.")
        print("Check the troubleshooting section in README.md")

    print("\n📚 For usage instructions, see README.md")
    print("🎯 For testing, run: python demo.py")

    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation interrupted by user.")
    except Exception as e:
        print(f"\n\nInstallation failed with error: {e}")
        print("Please check the error and try again, or install dependencies manually.")
