from taipy.gui import Gui, State
import pyaudio, numpy as np, scipy.fft
import pandas as pd
import threading
import time

CHUNK   = 1024          # samples per buffer (~23 ms @ 44.1 kHz)
RATE    = 44_100        # sampling rate
FORMAT  = pyaudio.paInt16
CHANNELS = 1

# Reactive state variables as pandas DataFrames
wave_data = pd.DataFrame({
    'time': np.arange(CHUNK),
    'amplitude': np.zeros(CHUNK)
})

spectrum_data = pd.DataFrame({
    'frequency': np.fft.rfftfreq(CHUNK, 1/RATE),
    'magnitude': np.zeros(CHUNK//2 + 1)
})

# Global variables for audio processing
audio_stream = None
audio_thread = None
stop_audio = False
gui_state = None

def audio_worker():
    """Worker thread for audio capture and processing"""
    global wave_data, spectrum_data, audio_stream, stop_audio, gui_state
    
    try:
        audio = pyaudio.PyAudio()
        audio_stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print("🎤 Audio recording started")
        
        while not stop_audio:
            try:
                # Read audio data
                data = audio_stream.read(CHUNK, exception_on_overflow=False)
                audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Update waveform data
                wave_data['amplitude'] = audio_array
                
                # Compute FFT and update spectrum data
                fft_data = scipy.fft.rfft(audio_array)
                magnitude_data = np.abs(fft_data)
                spectrum_data['magnitude'] = magnitude_data
                
                # Trigger GUI update if state is available
                if gui_state is not None:
                    try:
                        # Force GUI refresh by assigning new DataFrames
                        gui_state.assign("wave_data", wave_data.copy())
                        gui_state.assign("spectrum_data", spectrum_data.copy())
                    except Exception as e:
                        print(f"GUI update error: {e}")
                
                # Small delay to prevent overwhelming the GUI
                time.sleep(0.05)  # 50ms = ~20 FPS
                
            except Exception as e:
                print(f"Audio processing error: {e}")
                break
        
        # Cleanup
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        audio.terminate()
        print("🔇 Audio recording stopped")
        
    except Exception as e:
        print(f"Audio setup error: {e}")

def on_init(state: State):
    """Initialize the GUI and start audio processing"""
    global gui_state, audio_thread, stop_audio
    print("🎙️ Initializing audio visualization...")
    
    gui_state = state
    
    # Start audio processing thread
    stop_audio = False
    audio_thread = threading.Thread(target=audio_worker)
    audio_thread.daemon = True
    audio_thread.start()

def on_exit(state: State):
    """Clean up when application exits"""
    global stop_audio, audio_thread
    print("🛑 Shutting down...")
    stop_audio = True
    if audio_thread:
        audio_thread.join(timeout=1)

page = """
# 🎙️ Live Audio Monitor

## Waveform (Time Domain)
<|{wave_data}|chart|type=line|x=time|y=amplitude|title=Waveform|height=300px|>

## Spectrum (Frequency Domain)  
<|{spectrum_data}|chart|type=line|x=frequency|y=magnitude|title=Spectrum (FFT)|height=300px|>

*Speak into your microphone to see the real-time visualization!*
"""

if __name__ == "__main__":
    try:
        gui = Gui(page)
        gui.run(on_init=on_init, on_exit=on_exit, port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        stop_audio = True