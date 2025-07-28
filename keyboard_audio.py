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
audio_queue = queue.Queue(maxsize=5)
running = False
audio_thread = None
last_audio_level = 0.0
updates_count = 0

def audio_worker():
    """Background thread - captures audio and puts in queue"""
    global running, last_audio_level
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Recording started!")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            audio_level = np.max(np.abs(audio_data))
            last_audio_level = audio_level
            
            # Put audio data in queue
            if not audio_queue.full():
                audio_queue.put(audio_data)
            else:
                # Remove old data if queue is full
                try:
                    audio_queue.get_nowait()
                    audio_queue.put(audio_data)
                except queue.Empty:
                    pass
            
            # Show activity in console
            if audio_level > 0.01:
                print(f"🗣️  Audio: {audio_level:.4f}")
            
            time.sleep(0.1)  # 10 FPS capture
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def update_charts(state):
    """Update charts from queued audio data"""
    global wave_df, spec_df, updates_count
    
    try:
        # Get the most recent audio data
        latest_data = None
        count = 0
        
        while not audio_queue.empty():
            latest_data = audio_queue.get_nowait()
            count += 1
        
        if latest_data is not None:
            # Create new DataFrames
            new_wave_df = pd.DataFrame({'x': range(CHUNK), 'y': latest_data})
            fft_data = np.abs(np.fft.fft(latest_data)[:CHUNK//2])
            new_spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
            
            # Update state
            wave_df = new_wave_df
            spec_df = new_spec_df
            state.wave_df = new_wave_df
            state.spec_df = new_spec_df
            
            updates_count += 1
            print(f"✅ Updated! Processed {count} frames, Level: {last_audio_level:.4f}")
            
    except Exception as e:
        print(f"❌ Update error: {e}")

def start_recording(state):
    global running, audio_thread
    if not running:
        running = True
        audio_thread = threading.Thread(target=audio_worker)
        audio_thread.daemon = True
        audio_thread.start()
        print("🎬 Recording started! Press Space or click Refresh to update charts")

def stop_recording(state):
    global running
    running = False
    if audio_thread:
        audio_thread.join(timeout=2)

# Simple, clean interface
page = """
# 🎙️ Simple Audio Visualizer

<|Start|button|on_action=start_recording|>
<|Stop|button|on_action=stop_recording|>
<|**REFRESH CHARTS**|button|on_action=update_charts|>

## Audio Waveform
<|{wave_df}|chart|x=x|y=y|height=350px|>

## Frequency Spectrum
<|{spec_df}|chart|x=x|y=y|height=350px|>

**Status:** Level: <|{last_audio_level:.3f}|text|> | Updates: <|{updates_count}|text|> | Recording: <|{running}|text|>

---
**Instructions:**
1. Click "Start" 
2. Speak into microphone
3. Keep clicking "REFRESH CHARTS" to see real-time updates!

**Pro tip:** Click refresh rapidly while speaking for smooth animation!
"""

if __name__ == "__main__":
    print("🚀 Simple Audio Visualizer")
    print("💡 Click 'REFRESH CHARTS' rapidly while speaking for best results!")
    Gui(page).run(port=5000) 