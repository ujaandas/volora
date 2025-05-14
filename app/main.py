import time
import serial
import keyboard
import pyaudio
import numpy as np
import soxr
import pycodec2
import struct


def calculate_similarity(sent: bytes, received: bytes) -> float:
    if not sent and not received:
        return 100.0
    min_len = min(len(sent), len(received))
    matches = sum(1 for i in range(min_len) if sent[i] == received[i])
    similarity = matches / max(len(sent), len(received)) * 100
    return similarity


START_TOKEN = "bananariptide123"
END_TOKEN = "cooliobroskiomg"
CHUNK_SIZE = 128


def serial_send(ser, data):
    full_message = START_TOKEN.encode() + data + END_TOKEN.encode()
    for i in range(0, len(full_message), CHUNK_SIZE):
        chunk = full_message[i : i + CHUNK_SIZE] + b"\n"
        ser.write(chunk)
        ser.flush()
        time.sleep(0.1)
    print(f"[Sent] {len(data)} bytes of data.")


def serial_read(ser):
    buffer = b""
    start_token = START_TOKEN.encode()
    end_token = END_TOKEN.encode()
    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            buffer += data
            if start_token in buffer and end_token in buffer:
                start_idx = buffer.find(start_token) + len(start_token)
                end_idx = buffer.find(end_token)
                if start_idx < end_idx:
                    message = buffer[start_idx:end_idx]
                    buffer = buffer[end_idx + len(end_token) :]
                    return message
        time.sleep(0.01)


def main():
    try:
        ser1 = serial.Serial(port="/dev/tty.usbserial-0001", baudrate=115200, timeout=1)
        ser2 = serial.Serial(port="/dev/tty.usbserial-4", baudrate=115200, timeout=1)
    except Exception as e:
        print("Error opening serial port:", e)
        return

    p1 = pyaudio.PyAudio()
    c2 = pycodec2.Codec2(1200)
    pkt_size = c2.samples_per_frame() * 2
    pkt_fmt = "{}h".format(c2.samples_per_frame())

    last_sent_data = None

    def record_audio():
        print("Recording started...")
        s1 = p1.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
        )
        frames = []
        try:
            while keyboard.is_pressed("space"):
                data = s1.read(1024)
                frames.append(data)
        finally:
            print("Recording stopped.")
            s1.stop_stream()
            s1.close()
        return b"".join(frames)

    def downsample(audio_data, input_rate=44100, output_rate=8000):
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        downsampled_audio = soxr.resample(audio_array, input_rate, output_rate)
        return downsampled_audio.tobytes()

    def encode_audio(audio_data):
        print("Encoding audio with Codec2...")
        encoded_frames = []

        for i in range(0, len(audio_data), pkt_size):
            packet = audio_data[i : i + pkt_size]
            if len(packet) != pkt_size:
                break
            samples = np.array(struct.unpack(pkt_fmt, packet), dtype=np.int16)
            encoded_frames.append(c2.encode(samples))
        return b"".join(encoded_frames)

    def decode_audio(encoded_data):
        print("Decoding audio with Codec2...")
        decoded_samples = []
        encoded_frame_size = c2.bits_per_frame() // 8
        for i in range(0, len(encoded_data), encoded_frame_size):
            encoded_frame = encoded_data[i : i + encoded_frame_size]
            if len(encoded_frame) != encoded_frame_size:
                break
            decoded_samples.append(c2.decode(encoded_frame))
        decoded_audio = np.concatenate(decoded_samples).astype(np.int16)
        return decoded_audio.tobytes()

    def playback(data, rate=8000):
        print("Playing back received data...")
        s2 = p1.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            output=True,
        )
        s2.write(data)
        s2.stop_stream()
        s2.close()

    print("Starting walkie-talkie mode...")
    try:
        while True:
            if keyboard.is_pressed("space"):
                time.sleep(0.01)
                audio_data = record_audio()
                print(f"Captured {len(audio_data)} bytes of audio data.")
                print("Downsampling audio data...")
                downsampled_data = downsample(audio_data)
                print(f"Downsampled audio to {len(downsampled_data)} bytes.")
                encoded_data = encode_audio(downsampled_data)
                print(f"Encoded audio to {len(encoded_data)} bytes.")
                print("Sending encoded audio data over serial...")
                last_sent_data = encoded_data
                serial_send(ser1, encoded_data)

            if ser2.in_waiting:
                print("Receiving encoded audio data from serial...")
                incoming_encoded_data = serial_read(ser2)
                print(
                    f"Received complete message of length {len(incoming_encoded_data)} bytes."
                )
                if last_sent_data is not None:
                    similarity = calculate_similarity(
                        last_sent_data, incoming_encoded_data
                    )
                    print(
                        f"Similarity between sent and received data: {similarity:.2f}%"
                    )
                try:
                    decoded_audio = decode_audio(incoming_encoded_data)
                    print(f"Decoded audio to {len(decoded_audio)} bytes.")
                    playback(decoded_audio, rate=8000)
                except Exception as e:
                    print("Error decoding audio:", e)

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser1.close()
        ser2.close()
        p1.terminate()


if __name__ == "__main__":
    main()
