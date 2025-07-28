#!/usr/bin/env python3
"""
Taipy GUI - Working Audio Demo

A simple, reliable version that should work.
"""

from taipy.gui import Gui, State
import pyaudio
import numpy as np
import pandas as pd
import threading
import time

# Audio configuration
CHUNK = 512  # Smaller chunk for better performance
RATE = 44_100
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Global state
waveform_data = pd.DataFrame({
    'time': np.arange(CHUNK),
    'amplitude': np.zeros(CHUNK)
})

spectrum_data = pd.DataFrame({
    'frequency': np.linspace(0, RATE//2, CHUNK//2),
    'magnitude': np.zeros(CHUNK//2)
})

recording_status = "Stopped"
audio_thread = None
stop_thread = False

def audio_worker():
    """Worker thread for audio capture"""
    global waveform_data, spectrum_data, recording_status, stop_thread
    
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        recording_status = "Recording"
        print("✅ Audio recording started")
        
        while not stop_thread:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Update waveform data
                waveform_data['amplitude'] = audio_data
                
                # Compute FFT
                fft_data = np.fft.fft(audio_data)
                magnitude_data = np.abs(fft_data[:CHUNK//2])
                spectrum_data['magnitude'] = magnitude_data
                
                time.sleep(0.1)  # Update every 100ms
                
            except Exception as e:
                print(f"Audio processing error: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        recording_status = "Stopped"
        print("🔇 Audio recording stopped")
        
    except Exception as e:
        print(f"Audio setup error: {e}")
        recording_status = "Error"

def start_audio():
    """Start audio recording"""
    global audio_thread, stop_thread
    stop_thread = False
    audio_thread = threading.Thread(target=audio_worker)
    audio_thread.daemon = True
    audio_thread.start()

def stop_audio():
    """Stop audio recording"""
    global stop_thread
    stop_thread = True
    if audio_thread:
        audio_thread.join(timeout=1)

def on_init(state):
    """Initialize the application"""
    print("🎙️  Taipy GUI - Working Audio Demo")
    print("=" * 40)
    start_audio()
    print("🎤 Speak into your microphone to see the visualization")
    print("🌐 Opening browser at http://localhost:8080")

def on_exit(state):
    """Clean up when application exits"""
    stop_audio()

# Taipy GUI page
page = """
# Working Real-Time Audio Visualization

## Waveform (Time Domain)
<|{waveform_data}|chart|type=scatter|x=time|y=amplitude|height=300px|>

## Spectrum (Frequency Domain)
<|{spectrum_data}|chart|type=scatter|x=frequency|y=magnitude|height=300px|>

## Status
Recording: <|{recording_status}|text|>
"""

# Create and run the GUI
if __name__ == "__main__":
    try:
        gui = Gui(page=page)
        gui.run(
            title="Working Taipy Audio Demo",
            port=8080,
            on_init=on_init,
            on_exit=on_exit
        )
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        stop_audio()
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        stop_audio() 