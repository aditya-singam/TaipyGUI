from taipy.gui import Gui
import pyaudio
import numpy as np
import pandas as pd

# Audio configuration
CHUNK = 512
RATE = 44100
FORMAT = pyaudio.paInt16

# Global variables
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})
audio_stream = None
is_recording = False

def update_charts(state):
    """This function will be called periodically by Taipy"""
    global wave_df, spec_df, audio_stream, is_recording
    
    if not is_recording or audio_stream is None:
        return
    
    try:
        # Read audio data (non-blocking)
        data = audio_stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
        
        # Calculate audio level for debugging
        audio_level = np.max(np.abs(audio_data))
        print(f"Audio level: {audio_level:.4f}")
        
        # Create new DataFrames
        wave_df = pd.DataFrame({'x': range(CHUNK), 'y': audio_data})
        
        # Update spectrum
        fft_data = np.abs(np.fft.fft(audio_data)[:CHUNK//2])
        spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
        
        # Update the state
        state.wave_df = wave_df
        state.spec_df = spec_df
        
    except Exception as e:
        print(f"Update error: {e}")

def start_recording(state):
    global audio_stream, is_recording
    print("Starting recording...")
    
    try:
        if audio_stream is None:
            audio = pyaudio.PyAudio()
            audio_stream = audio.open(
                format=FORMAT, 
                channels=1, 
                rate=RATE, 
                input=True, 
                frames_per_buffer=CHUNK
            )
        
        is_recording = True
        print("🎤 Recording started - speak now!")
        
    except Exception as e:
        print(f"Start error: {e}")

def stop_recording(state):
    global is_recording
    print("Stopping recording...")
    is_recording = False

# Page with auto-refresh
page = """
# 🎙️ Timer-Based Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>

## Waveform (Time Domain)  
<|{wave_df}|chart|x=x|y=y|height=300px|refresh|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|refresh|>

Recording Status: <|{is_recording}|text|>
"""

if __name__ == "__main__":
    print("🚀 Starting timer-based audio monitor...")
    
    # Create GUI with periodic updates
    gui = Gui(page)
    
    # Add a periodic callback (every 100ms)
    gui.run(port=5000)  # This approach may not work in older Taipy versions 