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

# Voice activity detection threshold
VOICE_THRESHOLD = 0.01  # Adjust this if needed (higher = less sensitive)

# Global data
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})

# Thread communication
audio_queue = queue.Queue(maxsize=10)  # Limit queue size
running = False
audio_thread = None
gui_state = None
last_audio_level = 0.0

def audio_worker():
    """Background thread - captures audio with voice activity detection"""
    global running, last_audio_level
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Recording started - speak now!")
    print(f"📊 Voice threshold: {VOICE_THRESHOLD} (adjust if too sensitive)")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            audio_level = np.max(np.abs(audio_data))
            last_audio_level = audio_level
            
            # Only queue data if voice activity detected
            if audio_level > VOICE_THRESHOLD:
                if not audio_queue.full():
                    audio_queue.put(audio_data)
                    print(f"🗣️  Voice detected! Level: {audio_level:.4f}")
                else:
                    # Remove old data if queue is full
                    try:
                        audio_queue.get_nowait()
                        audio_queue.put(audio_data)
                    except queue.Empty:
                        pass
            else:
                # Low activity - put silence to show baseline
                if audio_queue.qsize() < 2:  # Keep some baseline data
                    if not audio_queue.full():
                        audio_queue.put(audio_data)
            
            time.sleep(0.05)  # 20 FPS
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def update_charts_auto():
    """Automatic chart updates - called periodically"""
    global wave_df, spec_df, gui_state, last_audio_level
    
    if gui_state is None or not running:
        return
    
    try:
        # Get most recent audio data
        latest_data = None
        while not audio_queue.empty():
            latest_data = audio_queue.get_nowait()
        
        if latest_data is not None:
            # Update waveform
            new_wave_df = pd.DataFrame({'x': range(CHUNK), 'y': latest_data})
            
            # Update spectrum
            fft_data = np.abs(np.fft.fft(latest_data)[:CHUNK//2])
            new_spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
            
            # Update GUI
            wave_df = new_wave_df
            spec_df = new_spec_df
            gui_state.wave_df = new_wave_df
            gui_state.spec_df = new_spec_df
            
            print(f"📈 Charts updated! Audio level: {last_audio_level:.4f}")
            
    except queue.Empty:
        pass
    except Exception as e:
        print(f"Auto update error: {e}")

def start_recording(state):
    global running, audio_thread, gui_state
    print("🎬 Starting automatic recording...")
    gui_state = state
    
    if not running:
        running = True
        audio_thread = threading.Thread(target=audio_worker)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Start automatic updates using a timer thread
        update_thread = threading.Thread(target=auto_update_loop)
        update_thread.daemon = True
        update_thread.start()

def auto_update_loop():
    """Automatic update loop running in separate thread"""
    while running:
        try:
            update_charts_auto()
            time.sleep(0.1)  # Update every 100ms
        except Exception as e:
            print(f"Update loop error: {e}")
        
def stop_recording(state):
    global running
    print("⏹️  Stopping recording...")
    running = False
    if audio_thread:
        audio_thread.join(timeout=2)

def adjust_threshold(state, var_name, value):
    """Adjust voice detection sensitivity"""
    global VOICE_THRESHOLD
    VOICE_THRESHOLD = value
    print(f"🎚️  Voice threshold adjusted to: {VOICE_THRESHOLD:.4f}")

# Global threshold control
threshold_value = VOICE_THRESHOLD

page = """
# 🎙️ Automatic Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>

**Voice Sensitivity:** <|{threshold_value}|slider|min=0.001|max=0.1|step=0.001|on_change=adjust_threshold|>

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Status:**
- Current Audio Level: <|{last_audio_level:.4f}|text|>
- Voice Threshold: <|{VOICE_THRESHOLD:.4f}|text|>
- Queue Size: <|{audio_queue.qsize() if running else 0}|text|>
- Recording: <|{running}|text|>

**Tips:**
- Adjust sensitivity slider if too sensitive/not sensitive enough
- Speak clearly for best results
- Charts update automatically when voice detected
"""

if __name__ == "__main__":
    print("🚀 Starting automatic audio monitor with voice detection...")
    Gui(page).run(port=5000) 