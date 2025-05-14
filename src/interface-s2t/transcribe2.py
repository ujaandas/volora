from vosk import Model, KaldiRecognizer
import wave
import json

# Path to the downloaded model directory
model = Model("vosk-model-small-en-us-0.15")

# Open your WAV file
wf = wave.open("output2.wav", "rb")

# Make sure audio format is correct
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
    raise ValueError("Audio file must be WAV format Mono PCM 16kHz")

rec = KaldiRecognizer(model, wf.getframerate())

# Read data in chunks and recognize
results = []
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        results.append(json.loads(rec.Result()))

# Final result
results.append(json.loads(rec.FinalResult()))

# Print all recognized text
full_text = " ".join([res.get("text", "") for res in results])
print("Recognized Text:")
print(full_text)
