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

# Global data - start with empty/zero data
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})

# Thread communication
audio_queue = queue.Queue()
running = False
audio_thread = None
is_recording = False

def audio_worker():
    """Background thread - captures audio only"""
    global running, is_recording
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Audio thread started")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            
            # Only put data in queue if we're actively recording
            if is_recording and running:
                if not audio_queue.full():
                    audio_queue.put(audio_data)
                
                audio_level = np.max(np.abs(audio_data))
                if audio_level > 0.01:
                    print(f"🎤 Capturing: {audio_level:.4f}")
            
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Audio thread stopped")

def start_recording(state):
    global running, audio_thread, is_recording
    print("▶️ START clicked")
    
    if not running:
        # Start audio thread
        running = True
        is_recording = True
        audio_thread = threading.Thread(target=audio_worker)
        audio_thread.daemon = True
        audio_thread.start()
        print("✅ Recording started - click 'Update Charts' to see live audio!")
    else:
        print("Already running!")

def stop_recording(state):
    global running, is_recording, audio_queue
    print("⏹️ STOP clicked")
    
    # Stop recording and clear queue
    is_recording = False
    running = False
    
    # Clear any remaining audio data from queue
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break
    
    print("🧹 Audio queue cleared")
    
    # Wait for thread to finish
    if audio_thread:
        audio_thread.join(timeout=2)
        print("✅ Recording fully stopped")

def update_charts(state):
    """Update charts with current audio data"""
    global wave_df, spec_df
    
    if not is_recording:
        print("📵 Not recording - no updates")
        return
    
    try:
        # Get most recent audio data
        latest_data = None
        processed = 0
        
        while not audio_queue.empty():
            latest_data = audio_queue.get_nowait()
            processed += 1
        
        if latest_data is not None:
            # Create new charts
            new_wave_df = pd.DataFrame({'x': range(CHUNK), 'y': latest_data})
            fft_data = np.abs(np.fft.fft(latest_data)[:CHUNK//2])
            new_spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
            
            # Update state
            wave_df = new_wave_df
            spec_df = new_spec_df
            state.wave_df = new_wave_df
            state.spec_df = new_spec_df
            
            audio_level = np.max(np.abs(latest_data))
            print(f"📊 Charts updated! Level: {audio_level:.4f} (processed {processed} frames)")
        else:
            print("📭 No audio data in queue")
            
    except Exception as e:
        print(f"❌ Update error: {e}")

def reset_charts(state):
    """Reset charts to zero/empty state"""
    global wave_df, spec_df
    
    wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
    spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})
    
    state.wave_df = wave_df
    state.spec_df = spec_df
    
    print("🔄 Charts reset to zero")

# Clean, simple interface
page = """
# 🎙️ Fixed Audio Monitor

<|▶️ START|button|on_action=start_recording|>
<|⏹️ STOP|button|on_action=stop_recording|>
<|📊 UPDATE CHARTS|button|on_action=update_charts|>
<|🔄 RESET|button|on_action=reset_charts|>

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Status:** Recording: <|{is_recording}|text|> | Queue: <|{audio_queue.qsize()}|text|>

**How to use:**
1. Click "▶️ START" to begin recording
2. Speak into your microphone  
3. Keep clicking "📊 UPDATE CHARTS" to see live visualization
4. Click "⏹️ STOP" to stop (charts will stop updating)
5. Click "🔄 RESET" to clear charts

**Note:** Charts only update when recording is active!
"""

if __name__ == "__main__":
    print("🚀 Fixed Audio Monitor")
    print("💡 Proper start/stop control with queue management!")
    Gui(page).run(port=5000) 