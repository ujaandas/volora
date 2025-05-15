import struct
import argparse
import numpy as np
import soxr
import serial
import time
import threading
import keyboard
from pyaudio import PyAudio, paInt16
from pycodec2 import Codec2

START_TOKEN = "bananariptide123"
END_TOKEN = "cooliobroskiomg"
CHUNK_SIZE = 128

AUDIO_CONFIG = {
    "input_rate": 44100,
    "output_rate": 8000,
    "channels": 1,
    "format": paInt16,
    "buffer_size": 1024,
    "record_seconds": 3,
}


def record_and_write_file(ser, c2):
    p = PyAudio()
    stream = p.open(
        format=AUDIO_CONFIG["format"],
        channels=AUDIO_CONFIG["channels"],
        rate=AUDIO_CONFIG["input_rate"],
        input=True,
        frames_per_buffer=AUDIO_CONFIG["buffer_size"],
    )
    print("Recording audio...")
    num_frames = int(
        AUDIO_CONFIG["input_rate"]
        / AUDIO_CONFIG["buffer_size"]
        * AUDIO_CONFIG["record_seconds"]
    )
    frames = [stream.read(AUDIO_CONFIG["buffer_size"]) for _ in range(num_frames)]
    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Downsampling audio...")
    audio_arr = np.frombuffer(b"".join(frames), dtype=np.int16)
    downsampled_bytes = soxr.resample(
        audio_arr, AUDIO_CONFIG["input_rate"], AUDIO_CONFIG["output_rate"]
    ).tobytes()
    print("Encoding audio with Codec2...")
    samples_per_frame = c2.samples_per_frame()
    pkt_struct = f"{samples_per_frame}h"
    encoded_frames = []
    frame_byte_size = 2 * samples_per_frame
    for i in range(0, len(downsampled_bytes), frame_byte_size):
        packet = downsampled_bytes[i : i + frame_byte_size]
        if len(packet) != frame_byte_size:
            print(f"Skipping incomplete frame at index {i}")
            break
        samples = np.array(struct.unpack(pkt_struct, packet), dtype=np.int16)
        encoded_frames.append(c2.encode(samples))
    data_hex = "".join(frame.hex() for frame in encoded_frames)
    with open("audio.hex", "wb") as f:
        f.write(data_hex.encode())
    print(f"Original data length (raw binary): {len(b''.join(encoded_frames))} bytes")
    print(f"Hex string length (to be sent in chunks): {len(data_hex)} characters")


def read_and_send_serial(ser, filename="audio.hex"):
    with open(filename, "rb") as f:
        raw_data = f.read()
    full_message = START_TOKEN.encode() + raw_data + END_TOKEN.encode()
    for i in range(0, len(full_message), CHUNK_SIZE):
        chunk = full_message[i : i + CHUNK_SIZE] + b"\n"
        ser.write(chunk)
        ser.flush()
        time.sleep(0.1)
    print(f"Sent {len(raw_data)} bytes from '{filename}'")


def serial_read_loop(ser):
    received_buffer = b""
    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            received_buffer += data
            while (
                START_TOKEN.encode() in received_buffer
                and END_TOKEN.encode() in received_buffer
            ):
                start_idx = received_buffer.find(START_TOKEN.encode()) + len(
                    START_TOKEN
                )
                end_idx = received_buffer.find(END_TOKEN.encode())
                if start_idx < end_idx:
                    message = received_buffer[start_idx:end_idx].strip()
                    with open("audio.raw", "wb") as f:
                        f.write(message)
                    print("Received and decoding audio")
                    decode_and_play_audio("audio.raw")
                    received_buffer = received_buffer[end_idx + len(END_TOKEN) :]
        time.sleep(0.01)


def decode_audio(encoded_data, c2):
    print("Decoding audio with Codec2...")
    decoded_samples = []
    frame_size = c2.bits_per_frame() // 8
    for i in range(0, len(encoded_data), frame_size):
        frame = encoded_data[i : i + frame_size]
        if len(frame) != frame_size:
            break
        decoded_samples.append(c2.decode(frame))
    if not decoded_samples:
        raise Exception("No complete frames were decoded.")
    return np.concatenate(decoded_samples).astype(np.int16).tobytes()


def decode_and_play_audio(filename="audio.raw"):
    with open(filename, "rb") as f:
        hex_data = f.read()
    encoded_data = bytes.fromhex(hex_data.decode().strip())
    c2 = Codec2(1200)
    audio_bytes = decode_audio(encoded_data, c2)
    p = PyAudio()
    stream = p.open(
        format=AUDIO_CONFIG["format"],
        channels=AUDIO_CONFIG["channels"],
        rate=AUDIO_CONFIG["output_rate"],
        output=True,
    )
    print("Playing audio...")
    stream.write(audio_bytes)
    stream.stop_stream()
    stream.close()
    p.terminate()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttys005")
    parser.add_argument("--key", default="space")
    args = parser.parse_args()
    print(f"Using serial port: {args.port}...")
    ser = serial.Serial(args.port, baudrate=115200, timeout=1)
    c2 = Codec2(1200)
    threading.Thread(target=serial_read_loop, args=(ser,), daemon=True).start()
    while True:
        if keyboard.is_pressed(args.key):
            record_and_write_file(ser, c2)
            read_and_send_serial(ser)
            while keyboard.is_pressed(args.key):
                time.sleep(0.1)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
