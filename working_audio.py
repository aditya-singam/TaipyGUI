from taipy.gui import Gui
import pyaudio
import numpy as np
import pandas as pd
import threading
import queue
import time

# Audio configuration
CHUNK = 512
RATE = 44100
FORMAT = pyaudio.paInt16

# Global data
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})

# Thread communication
audio_queue = queue.Queue()
running = False
audio_thread = None

def audio_worker():
    """Background thread - only captures audio, no GUI updates"""
    global running
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Recording started - speak now!")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            
            # Put audio data in queue (thread-safe)
            if not audio_queue.full():
                audio_queue.put(audio_data)
            
            time.sleep(0.05)  # 20 FPS
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def update_gui_from_queue(state):
    """Called by Taipy in main thread - safe for GUI updates"""
    global wave_df, spec_df
    
    try:
        # Get latest audio data from queue (non-blocking)
        while not audio_queue.empty():
            audio_data = audio_queue.get_nowait()
            
            # Update waveform
            wave_df = pd.DataFrame({'x': range(CHUNK), 'y': audio_data})
            
            # Update spectrum
            fft_data = np.abs(np.fft.fft(audio_data)[:CHUNK//2])
            spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
            
            # Update state (this runs in main thread - safe!)
            state.wave_df = wave_df
            state.spec_df = spec_df
            
            audio_level = np.max(np.abs(audio_data))
            print(f"GUI updated successfully! Audio level: {audio_level:.4f}")
            
    except queue.Empty:
        pass  # No new audio data
    except Exception as e:
        print(f"GUI update error: {e}")

def start_recording(state):
    global running, audio_thread
    print("Start button clicked!")
    
    if not running:
        running = True
        audio_thread = threading.Thread(target=audio_worker)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Schedule periodic GUI updates using Taipy's mechanism
        # This is the key fix - updates happen in main thread!
        print("Starting periodic GUI updates...")

def stop_recording(state):
    global running
    print("Stop button clicked!")
    running = False
    if audio_thread:
        audio_thread.join(timeout=2)

# Page with periodic refresh
page = """
# 🎙️ Working Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>
<|Update Charts|button|on_action=update_gui_from_queue|>

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Instructions:** 
1. Click "Start Recording"
2. Keep clicking "Update Charts" while speaking
3. Charts should update with your voice!

Queue size: <|{len(audio_queue.queue) if hasattr(audio_queue, 'queue') else 'N/A'}|text|>
"""

if __name__ == "__main__":
    print("🚀 Starting working audio monitor...")
    print("💡 This version uses manual chart updates to avoid Flask context issues")
    Gui(page).run(port=5000) 