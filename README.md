# 🎙️ Taipy GUI Real-Time Audio Visualizer

A real-time audio waveform and spectrum analyzer built with **Taipy GUI** and **PyAudio**. This application captures microphone input and displays both time-domain waveforms and frequency-domain spectrum visualizations in an interactive web interface.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Taipy](https://img.shields.io/badge/taipy-GUI-orange)
![PyAudio](https://img.shields.io/badge/PyAudio-enabled-green)

## ✨ Features

- 🎤 **Real-time microphone capture** using PyAudio
- 📊 **Dual visualization**: Time-domain waveform + Frequency spectrum (FFT)
- 🌐 **Web-based interface** powered by Taipy GUI
- ⏯️ **Start/Stop controls** with proper thread management
- 🔄 **Manual refresh** system (avoids Flask context issues)
- 🧹 **Clean shutdown** with queue management
- 📱 **Responsive design** with modern UI components

## 🛠️ Installation

### Prerequisites

- **Python 3.9 or higher** (3.11 recommended for best Taipy compatibility)
- **macOS/Linux/Windows** with microphone access
- **Homebrew** (macOS only, for PortAudio dependency)

### Step 1: Install System Dependencies

**On macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PortAudio (required for PyAudio)
brew install portaudio
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**On Windows:**
```bash
# PyAudio wheels are usually available, no additional setup needed
```

### Step 2: Set Up Python Environment

```bash
# Clone or download this repository
cd TaipyGUI

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install taipy pyaudio numpy pandas scipy
```

## 🚀 Quick Start

1. **Activate your virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Run the application:**
   ```bash
   python3 fixed_audio.py
   ```

3. **Open your browser:**
   - Navigate to `http://localhost:5000`

4. **Start visualizing:**
   - Click **"▶️ START"** to begin audio capture
   - **Speak into your microphone**
   - Click **"📊 UPDATE CHARTS"** repeatedly to see real-time updates
   - Click **"⏹️ STOP"** when finished

## 📖 How to Use

### Interface Controls

| Button | Function |
|--------|----------|
| **▶️ START** | Begin microphone capture |
| **⏹️ STOP** | Stop capture and clear audio queue |
| **📊 UPDATE CHARTS** | Refresh visualizations with latest audio |
| **🔄 RESET** | Clear charts back to zero state |

### Workflow

1. **Start Recording**: Click "▶️ START" - you'll see console message "✅ Recording started"
2. **Speak/Make Sound**: Talk into your microphone (watch console for "🎤 Capturing: X.XXXX")
3. **Update Visualization**: Click "📊 UPDATE CHARTS" repeatedly while speaking
4. **Observe Charts**:
   - **Waveform**: Shows audio signal amplitude over time
   - **Spectrum**: Shows frequency content (FFT) of your voice
5. **Stop When Done**: Click "⏹️ STOP" to end session

### Tips for Best Results

- **Click UPDATE rapidly** (5-10 times per second) for smooth real-time animation
- **Speak clearly** and at normal volume
- **Watch the console** for audio level feedback
- **Adjust microphone permissions** if needed (System Preferences → Privacy & Security → Microphone)

## 🔧 Technical Details

### Architecture

- **Backend**: Python with PyAudio for audio capture
- **Frontend**: Taipy GUI (React-based) for web interface  
- **Threading**: Background audio capture + main thread GUI updates
- **Data Flow**: Audio → Queue → DataFrame → Chart Updates

### Audio Configuration

```python
CHUNK = 512          # Samples per buffer (~11ms at 44.1kHz)
RATE = 44100         # Sampling rate (44.1kHz)
FORMAT = paInt16     # 16-bit audio
CHANNELS = 1         # Mono capture
```

### Why Manual Updates?

This implementation uses manual chart updates instead of automatic refresh to avoid **Flask application context errors** that occur when background threads try to update the GUI directly. The queue-based approach ensures thread-safe communication between audio capture and visualization.

## 📁 Project Structure

```
TaipyGUI/
├── fixed_audio.py          # ✅ Main application (working version)
├── README.md               # 📖 This documentation
├── taipy_audio_working.py  # 🔧 Alternative threading implementation  
├── debug_audio.py          # 🐛 Console-only audio level tester
├── simple_audio.py         # 🧪 Simplified test version
└── py_ui_taipy_audio_wf_v_2.md  # 📝 Original tutorial notes
```

## 🐛 Troubleshooting

### Common Issues

**❌ "ModuleNotFoundError: No module named 'pyaudio'"**
- Solution: Make sure virtual environment is activated and PyAudio is installed
- macOS: Install PortAudio first (`brew install portaudio`)

**❌ "Working outside of application context"**  
- Solution: Use `fixed_audio.py` (not auto-updating versions)
- This error occurs with background thread GUI updates

**❌ Charts not updating**
- Check console for "🎤 Capturing: X.XXXX" messages when speaking
- Ensure microphone permissions are granted to Terminal/Python
- Try adjusting microphone volume/sensitivity

**❌ No audio detected**
- Test with: `python3 debug_audio.py` (shows audio levels in console)
- Check System Preferences → Sound → Input for microphone selection
- Verify microphone is not muted

**❌ "Permission denied" or microphone access**
- macOS: System Preferences → Privacy & Security → Microphone → Enable for Terminal
- Test microphone in other apps first

### Performance Tips

- **Reduce latency**: Decrease `CHUNK` size (trade-off with CPU usage)
- **Smoother spectrum**: Increase `CHUNK` size for better frequency resolution  
- **Lower CPU**: Increase `time.sleep()` values in audio worker thread

## 🎯 Advanced Usage

### Customization Options

You can modify these parameters in `fixed_audio.py`:

```python
# Audio settings
CHUNK = 512          # Buffer size (latency vs. quality)
RATE = 44100         # Sample rate (quality vs. processing)

# Voice activity detection (if implemented)
VOICE_THRESHOLD = 0.01  # Minimum level to consider "voice"
```

### Adding Features

The modular design makes it easy to add:
- 🎚️ **Volume controls** and gain adjustment
- 🎨 **Visual themes** and chart styling  
- 💾 **Recording/export** functionality
- 🔊 **Multiple audio sources** selection
- 📊 **Advanced DSP** (filters, effects)

## 📚 References

- [Taipy Documentation](https://docs.taipy.io/)
- [PyAudio Tutorial](https://people.csail.mit.edu/hubert/pyaudio/)
- [NumPy FFT Documentation](https://numpy.org/doc/stable/reference/routines.fft.html)
- [Pandas DataFrame Guide](https://pandas.pydata.org/docs/user_guide/dsintro.html#dataframe)

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this audio visualizer!

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

---

**Built with ❤️ using Taipy GUI, PyAudio, and Python** 