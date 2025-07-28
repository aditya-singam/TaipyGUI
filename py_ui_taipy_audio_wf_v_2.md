Tags: #gui, #taipy, #audio, #pyaudio, #visualization

```toc
style: number
min_depth: 1
max_depth: 6
```

# Taipy GUI — Real‑Time Audio Waveform & Spectrum

## Introduction

**Taipy GUI** is the front‑end module of the open‑source Taipy framework. It lets you build interactive web or desktop‑style dashboards ^purely^ in Python—no JavaScript, CSS, or Flask wiring required—by wrapping Plotly/Dash in a concise Markdown or builder syntax. Because its components are *reactive*, binding an updating NumPy array to a `<|chart|>` element automatically refreshes the plot, which is perfect for streaming audio visualisations.

This note shows how to capture microphone audio with **PyAudio** and visualise both its time‑domain waveform and frequency‑domain spectrum in real time using Taipy GUI.

---

## Installation

```sh
# 1️⃣  Create / activate your venv, then install Taipy GUI + audio deps
python3.11 -m venv .venv && source .venv/bin/activate
pip install taipy taipy[pyaudio] pyaudio numpy scipy
```

> **Tip (macOS):** If `pyaudio` fails during build, install PortAudio first: `brew install portaudio` then `pip install pyaudio`.

---

## Quick Start – 20‑Line Demo

The snippet below opens the default microphone, buffers ≈50 ms of samples, and updates two charts each callback:

```python
from taipy.gui import Gui, notify
import pyaudio, numpy as np, scipy.fft

CHUNK   = 1024          # samples per buffer (~23 ms @ 44.1 kHz)
RATE    = 44_100        # sampling rate
FORMAT  = pyaudio.paInt16
CHANNELS = 1

# Reactive state variables
wave = np.zeros(CHUNK)
freq = np.zeros(CHUNK//2)
mag  = np.zeros(CHUNK//2)

def audio_cb(in_data, *_):                # PyAudio → NumPy → state
    global wave, freq, mag
    wave = np.frombuffer(in_data, np.int16) / 32_768
    spec = scipy.fft.rfft(wave)
    freq = np.fft.rfftfreq(len(wave), 1/RATE)
    mag  = np.abs(spec)
    notify(state, "refresh")             # push changes to GUI
    return (in_data, pyaudio.paContinue)

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK,
                stream_callback=audio_cb)

page = """
# 🎙️ Live Audio Monitor
<|{wave}|chart|type=line|x=range(len(wave))|y=wave|title=Waveform|>
<|{mag}|chart|type=line|x=freq|y=mag|title=Spectrum (FFT)|>
"""

Gui(page).run()
```

Open the browser at [http://localhost:8080](http://localhost:8080) and speak—both plots update in near real time.

---

## Key Concepts

### 1. Reactive State

Every Taipy page has a `state` object. Mutating variables (e.g., `wave`, `mag`) and then calling `notify(state, "refresh")` triggers automatic chart updates.

### 2. Markdown vs. Builder Layouts

- **Markdown DSL** (`<|...|>`): fastest for prototypes (used above).
- **Python builder API** (`Gui(page_dict)`): preferable when you need conditions or loops during layout generation.

### 3. Plotly Under‑the‑Hood

Taipy charts map straight to Plotly traces; you can pass extra `key=value` trace parameters directly in the chart tag.

### 4. Performance Tips

- Reduce `CHUNK` for lower latency; increase for smoother spectra.
- Use `scipy.fft.rfft` (real FFT) to halve computation cost.
- Do heavy DSP in a worker thread or `asyncio` task and update state.

---

## Tutorial – Step by Step

### Step 1  Capture Audio

```python
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK,
                stream_callback=audio_cb)
```

`stream_callback` fires for each buffer, keeping GUI responsive.

### Step 2  Process Waveform & FFT

Inside `audio_cb`, convert bytes → NumPy → run an **RFFT** to get magnitude spectrum.

### Step 3  Bind Arrays to Charts

```python
<|{wave}|chart|type=line|x=range(len(wave))|y=wave|title=Waveform|>
```

### Step 4  Trigger UI Refresh

`notify(state, "refresh")` sends updated buffers to the browser.

### Step 5  Run & Verify

Run the script, open the tab, and observe plots responding to voice/music.

---

## Next Steps

- **UI controls**: add sliders for FFT window or gain.
- **VAD integration**: skip silence to reduce CPU usage.
- **Recording**: stream to WAV using `wave` or `soundfile`.

---

## ⚠️  Important: Python Version & Running Instructions

**Python Version Requirement:**
- **Use Python 3.11** for Taipy compatibility
- **Python 3.13 has known issues** with Taipy dependencies (SQLAlchemy compatibility errors)
- The demo will not work with Python 3.13

**To run the working demo:**
```bash
# Make sure you're using Python 3.11
python3.11 taipy_audio_working.py
```

**Demo URL:** [http://localhost:8080](http://localhost:8080)

---

## References

- Taipy docs – [https://docs.taipy.io/](https://docs.taipy.io/)
- PyAudio tutorial – [https://people.csail.mit.edu/hubert/pyaudio/](https://people.csail.mit.edu/hubert/pyaudio/)
- SciPy FFT docs – [https://docs.scipy.org/doc/scipy/reference/fft.html](https://docs.scipy.org/doc/scipy/reference/fft.html)

