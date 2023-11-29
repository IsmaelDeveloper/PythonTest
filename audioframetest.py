import sounddevice as sd
import numpy as np


def listen_microphone(duration=5, sample_rate=44100):
    # Record audio from the microphone
    audio_data = sd.rec(int(duration * sample_rate),
                        samplerate=sample_rate, channels=2, dtype=np.int16)
    sd.wait()

    # Normalize the audio data to the range [-1, 1]
    normalized_audio = audio_data / 32768.0

    return normalized_audio


# Example usage
audio_frame = listen_microphone()
print(audio_frame)
