import time
import os
import keyboard
import pyaudio
import numpy as np
import soxr
import pycodec2
import struct
import serial


START_TOKEN = "bananariptide123"
END_TOKEN = "cooliobroskiomg"
CHUNK_SIZE = 128


RECORD_FILE = "recorded_audio.raw"
SEND_CHANNEL_FILE = "send_channel.hex"
RECEIVED_CHANNEL_FILE = "received_channel.hex"


def serial_send(ser, data):
    full_message = START_TOKEN.encode() + data + END_TOKEN.encode()
    for i in range(0, len(full_message), CHUNK_SIZE):
        chunk = full_message[i : i + CHUNK_SIZE] + b"\n"
        ser.write(chunk)
        ser.flush()
        time.sleep(0.1)
    print(f"[Serial Send] Sent {len(data)} bytes of encoded data over serial.")


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


def file_send(data, filename=SEND_CHANNEL_FILE):
    full_message = START_TOKEN.encode() + data + END_TOKEN.encode()
    hex_message = full_message.hex()
    with open(filename, "w") as f:
        for i in range(0, len(hex_message), CHUNK_SIZE):
            chunk = hex_message[i : i + CHUNK_SIZE] + "\n"
            f.write(chunk)
            f.flush()
            time.sleep(0.1)
    print(f"[File Send] Written {len(data)} bytes of encoded data to '{filename}'.")


def file_read(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as f:
        hex_data = f.read().strip()
    if not hex_data:
        return None
    hex_data = hex_data.replace("\n", "")
    try:
        data = bytes.fromhex(hex_data)
    except Exception:
        return None

    start_token = START_TOKEN.encode()
    end_token = END_TOKEN.encode()
    start_idx = data.find(start_token)
    end_idx = data.find(end_token)
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
        return None
    message = data[start_idx + len(start_token) : end_idx]

    with open(filename, "w") as f:
        f.write("")
    return message


def write_channel_file(data, filename):
    full_message = START_TOKEN.encode() + data + END_TOKEN.encode()
    hex_message = full_message.hex()
    with open(filename, "w") as f:
        f.write(hex_message)
    print(f"[Channel File] Wrote received encoded data to '{filename}'.")


def record_audio_to_file(filename=RECORD_FILE):
    p = pyaudio.PyAudio()
    print("Recording started... (hold space)")
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
    )
    frames = []
    try:
        while keyboard.is_pressed("space"):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
    finally:
        print("Recording stopped.")
        stream.stop_stream()
        stream.close()
        p.terminate()
    raw_data = b"".join(frames)
    with open(filename, "wb") as f:
        f.write(raw_data)
    print(f"[Recording] Saved raw audio to '{filename}'")
    return filename


def downsample(audio_data, input_rate=44100, output_rate=8000):
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    downsampled_audio = soxr.resample(audio_array, input_rate, output_rate)
    return downsampled_audio.tobytes()


def encode_audio(audio_data, c2, packet_size, struct_fmt):
    print("Encoding audio with Codec2...")
    encoded_frames = []
    for i in range(0, len(audio_data), packet_size):
        packet = audio_data[i : i + packet_size]
        if len(packet) != packet_size:
            break
        samples = np.array(struct.unpack(struct_fmt, packet), dtype=np.int16)
        encoded_frames.append(c2.encode(samples))
    encoded = b"".join(encoded_frames)
    return encoded


def decode_audio(encoded_data, c2):
    print("Decoding audio with Codec2...")
    decoded_samples = []
    encoded_frame_size = c2.bits_per_frame() // 8
    for i in range(0, len(encoded_data), encoded_frame_size):
        encoded_frame = encoded_data[i : i + encoded_frame_size]
        if len(encoded_frame) != encoded_frame_size:
            break
        decoded_samples.append(c2.decode(encoded_frame))
    if decoded_samples:
        decoded_audio = np.concatenate(decoded_samples).astype(np.int16)
        return decoded_audio.tobytes()
    else:
        raise Exception("No complete frames were decoded.")


def playback(data, rate=8000):
    print("Playing back received audio...")
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, output=True)
    stream.write(data)
    stream.stop_stream()
    stream.close()
    p.terminate()


def main():
    c2 = pycodec2.Codec2(1200)
    INT16_BYTE_SIZE = 2
    PACKET_SIZE = c2.samples_per_frame() * INT16_BYTE_SIZE
    STRUCT_FORMAT = "{}h".format(c2.samples_per_frame())
    last_sent_data = None

    try:
        ser = serial.Serial(port="/dev/tty.usbserial-4", baudrate=115200, timeout=1)
    except Exception as e:
        print("Error opening serial port:", e)
        return

    print("Starting combined serial & file-based walkie-talkie mode...")
    try:
        while True:
            if keyboard.is_pressed("space"):
                record_audio_to_file(RECORD_FILE)

                with open(RECORD_FILE, "rb") as f:
                    audio_data = f.read()
                print(f"[Send] Read {len(audio_data)} bytes from '{RECORD_FILE}'.")
                downsampled_data = downsample(audio_data)
                print(f"[Send] Downsampled audio to {len(downsampled_data)} bytes.")
                encoded_data = encode_audio(
                    downsampled_data, c2, PACKET_SIZE, STRUCT_FORMAT
                )
                print(f"[Send] Encoded audio to {len(encoded_data)} bytes.")
                print(f"[Send] Encoded audio {encoded_data}")

                file_send(encoded_data, SEND_CHANNEL_FILE)

                to_send = file_read(SEND_CHANNEL_FILE)
                if to_send:
                    serial_send(ser, to_send)
                    last_sent_data = to_send
                time.sleep(0.5)

            if ser.in_waiting:
                received_payload = serial_read(ser)
                print(
                    f"[Serial Receive] Received {len(received_payload)} bytes of encoded data."
                )
                write_channel_file(received_payload, RECEIVED_CHANNEL_FILE)

                incoming_encoded = file_read(RECEIVED_CHANNEL_FILE)
                if incoming_encoded:
                    print(
                        f"[Receive] Extracted {len(incoming_encoded)} bytes from '{RECEIVED_CHANNEL_FILE}'."
                    )
                    if last_sent_data is not None:
                        similarity = (
                            sum(
                                1
                                for i, j in zip(last_sent_data, incoming_encoded)
                                if i == j
                            )
                            / max(len(last_sent_data), len(incoming_encoded))
                            * 100
                        )
                        print(
                            f"[Compare] Similarity between last sent and received data: {similarity:.2f}%"
                        )
                    try:
                        decoded_audio = decode_audio(incoming_encoded, c2)
                        print(f"[Receive] Received data {incoming_encoded}")
                        print(
                            f"[Receive] Decoded audio into {len(decoded_audio)} bytes."
                        )
                        playback(decoded_audio, rate=8000)
                    except Exception as e:
                        print("Error decoding received audio:", e)
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
