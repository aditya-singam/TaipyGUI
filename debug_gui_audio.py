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
    update_count = 0
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            
            # Calculate audio level for debugging
            audio_level = np.max(np.abs(audio_data))
            update_count += 1
            
            print(f"Update #{update_count}: Audio level = {audio_level:.4f}", end="")
            
            # Create NEW DataFrames
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
            
            # Update global variables
            wave_df = new_wave_df
            spec_df = new_spec_df
            
            # Try GUI update
            if gui_state is not None:
                try:
                    gui_state.assign("wave_df", new_wave_df)
                    gui_state.assign("spec_df", new_spec_df)
                    print(" | GUI updated ✅")
                except Exception as e:
                    print(f" | GUI error: {e}")
            else:
                print(" | No GUI state ❌")
            
            time.sleep(0.2)  # Slower updates for easier debugging
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def start_recording(state):
    global running, audio_thread, gui_state
    print(f"Start button clicked! State object: {state}")
    gui_state = state
    
    if not running:
        running = True
        audio_thread = threading.Thread(target=update_audio)
        audio_thread.daemon = True
        audio_thread.start()
        print("Audio thread started!")
    else:
        print("Already recording!")

def stop_recording(state):
    global running
    print("Stop button clicked!")
    running = False
    if audio_thread:
        audio_thread.join(timeout=2)
        print("Audio thread stopped!")

# Simple page with current values display
page = """
# 🎙️ Debug Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>

**Check the terminal/console for debug output!**

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Current wave_df max value:** <|{wave_df['y'].max() if len(wave_df) > 0 else 0}|text|>
**Current spec_df max value:** <|{spec_df['y'].max() if len(spec_df) > 0 else 0}|text|>
"""

if __name__ == "__main__":
    print("🚀 Starting debug audio monitor...")
    print("👀 Watch the console output when you click Start and speak!")
    Gui(page).run(port=5000) 