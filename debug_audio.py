import pyaudio
import numpy as np
import time

print("🎤 Debug Audio Test - Speak into your microphone!")
print("Press Ctrl+C to stop")

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

try:
    while True:
        data = stream.read(1024, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        amplitude = np.max(np.abs(audio_data))
        
        # Visual bar
        bar_length = int(amplitude / 1000)
        bar = "█" * min(bar_length, 50)
        
        print(f"Audio Level: {amplitude:5d} {bar}", end='\r')
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Stopped")
finally:
    stream.stop_stream()
    stream.close()
    audio.terminate() 