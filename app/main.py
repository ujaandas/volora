import pyaudio
import wave


def main():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16  # 16 bits per sample
    CHANNELS = 1
    RATE = 44100  # 44.1k samples/sec # try 500 for 8k bitrate
    # RATE = 500
    RECORD_SECONDS = 5  # 3s
    WAVE_OUTPUT_FILENAME = "input.wav"

    # total samples = RATE * RECORD_SECONDS = 44100 * 3 = 132300
    # total bits = total samples * 16 bits = 132300 * 16 = 2116800
    # bitrate = total bits / total seconds = 2116800 / 3 = 705600

    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    print(frames)
    print(len(frames))
    # print number of bits
    print(len(frames[0]))
    # print number of bytes
    print(len(frames[0]) / 8)

    wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()


if __name__ == "__main__":
    main()
