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
VOICE_THRESHOLD = 0.01

# Global data
wave_df = pd.DataFrame({'x': range(CHUNK), 'y': np.zeros(CHUNK)})
spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': np.zeros(CHUNK//2)})

# Thread communication
audio_queue = queue.Queue(maxsize=10)
running = False
audio_thread = None
last_audio_level = 0.0
updates_count = 0

def audio_worker():
    """Background thread - only captures audio and puts in queue"""
    global running, last_audio_level
    
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🎤 Recording started - speak now!")
    print(f"📊 Voice threshold: {VOICE_THRESHOLD}")
    
    while running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16) / 32768.0
            audio_level = np.max(np.abs(audio_data))
            last_audio_level = audio_level
            
            # Always put data in queue, but mark if it's voice activity
            audio_info = {
                'data': audio_data,
                'level': audio_level,
                'is_voice': audio_level > VOICE_THRESHOLD
            }
            
            if not audio_queue.full():
                audio_queue.put(audio_info)
            else:
                # Remove old data if queue is full
                try:
                    audio_queue.get_nowait()
                    audio_queue.put(audio_info)
                except queue.Empty:
                    pass
            
            if audio_level > VOICE_THRESHOLD:
                print(f"🗣️  Voice: {audio_level:.4f}")
            
            time.sleep(0.05)  # 20 FPS
            
        except Exception as e:
            print(f"Audio error: {e}")
            break
    
    stream.close()
    audio.terminate()
    print("🔇 Recording stopped")

def update_charts(state):
    """Manual update function - called when user clicks button"""
    global wave_df, spec_df, updates_count
    
    try:
        # Process ALL queued audio data
        latest_data = None
        processed_count = 0
        
        while not audio_queue.empty():
            audio_info = audio_queue.get_nowait()
            latest_data = audio_info['data']
            processed_count += 1
        
        if latest_data is not None:
            # Update waveform
            new_wave_df = pd.DataFrame({'x': range(CHUNK), 'y': latest_data})
            
            # Update spectrum
            fft_data = np.abs(np.fft.fft(latest_data)[:CHUNK//2])
            new_spec_df = pd.DataFrame({'x': range(CHUNK//2), 'y': fft_data})
            
            # Update global variables AND state
            wave_df = new_wave_df
            spec_df = new_spec_df
            state.wave_df = new_wave_df
            state.spec_df = new_spec_df
            
            updates_count += 1
            
            print(f"📈 Charts updated! Processed {processed_count} audio frames. Audio level: {last_audio_level:.4f}")
            return True
        else:
            print("📭 No new audio data to process")
            return False
            
    except queue.Empty:
        print("📭 Audio queue is empty")
        return False
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False

def start_recording(state):
    global running, audio_thread
    print("🎬 Starting recording...")
    
    if not running:
        running = True
        audio_thread = threading.Thread(target=audio_worker)
        audio_thread.daemon = True
        audio_thread.start()
        print("✅ Recording started! Click 'Refresh Charts' to see updates")

def stop_recording(state):
    global running
    print("⏹️  Stopping recording...")
    running = False
    if audio_thread:
        audio_thread.join(timeout=2)
    print("✅ Recording stopped")

def adjust_threshold(state, var_name, value):
    """Adjust voice detection sensitivity"""
    global VOICE_THRESHOLD
    VOICE_THRESHOLD = value
    print(f"🎚️  Voice threshold: {VOICE_THRESHOLD:.4f}")

# Global variables for display
threshold_value = VOICE_THRESHOLD

page = """
# 🎙️ Real-Time Audio Monitor

<|Start Recording|button|on_action=start_recording|>
<|Stop Recording|button|on_action=stop_recording|>
<|🔄 Refresh Charts|button|on_action=update_charts|>

**Voice Threshold:** <|{threshold_value}|slider|min=0.001|max=0.1|step=0.001|on_change=adjust_threshold|>

## Waveform (Time Domain)
<|{wave_df}|chart|x=x|y=y|height=300px|>

## Spectrum (Frequency Domain)
<|{spec_df}|chart|x=x|y=y|height=300px|>

**Live Status:**
- 🎤 Current Audio Level: <|{last_audio_level:.4f}|text|>
- 🎚️ Voice Threshold: <|{VOICE_THRESHOLD:.4f}|text|>
- 📊 Queue Size: <|{audio_queue.qsize() if running else 0}|text|>
- 🔄 Updates Count: <|{updates_count}|text|>
- ▶️ Recording: <|{running}|text|>

**Instructions:**
1. Click "Start Recording"
2. Speak into your microphone
3. Click "🔄 Refresh Charts" to see your voice!
4. Adjust threshold if needed
5. Keep clicking refresh for real-time updates

**Tip:** You can click refresh rapidly for near real-time updates!
"""

if __name__ == "__main__":
    print("🚀 Starting final audio monitor...")
    print("💡 This version uses the proven working approach!")
    Gui(page).run(port=5000) 