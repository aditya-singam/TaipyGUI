from taipy.gui import Gui
import pyaudio
import numpy as np
import pandas as pd
import threading
import time

# Audio configuration
CHUNK = 512
RATE = 44100
FORMAT = pyaudio.paInt16

# Global data
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})

# Thread control
running = False
audio_thread = None
gui_state = None

def update_audio():
    global wave_df, spec_df, running, gui_state
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Recording started - speak now!")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            
            # Create NEW DataFrames (don't modify in-place)
            new_wave_df = pd.DataFrame({
                'x': range(CHUNK), 
                'y': audio_data
            })
            
            # Update spectrum
            fft_data = np.abs(np.fft.fft(audio_data)[:CHUNK//2])
            new_spec_df = pd.DataFrame({
                'x': range(CHUNK//2), 
                'y': fft_data
            })
            
            # Update global variables AND notify GUI
            wave_df = new_wave_df
            spec_df = new_spec_df
            
            if gui_state is not None:
                try:
                    # Force GUI update by assigning new DataFrames
                    gui_state.assign("wave_df", new_wave_df)
                    gui_state.assign("spec_df", new_spec_df)
                except Exception as e:
                    print(f"GUI update error: {e}")
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def start_recording(state):
    global running, audio_thread, gui_state
    gui_state = state  # Capture the state object
    if not running:
        running = True
        audio_thread = threading.Thread(target=update_audio)
        audio_thread.daemon = True
        audio_thread.start()

def stop_recording(state):
    global running
    running = False
    if audio_thread:
        audio_thread.join(timeout=1)

# Simple page
page = """
# 🎙️ Simple Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Instructions:** Click "Start Recording" and speak into your microphone!
"""

if __name__ == "__main__":
    Gui(page).run(port=5000) 