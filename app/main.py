import struct
import argparse
from pyaudio import PyAudio, paInt16
import numpy as np
import soxr
from pycodec2 import Codec2
import serial
import time
import keyboard


def record_and_send(ser, c2):
    p = PyAudio()
    stream = p.open(
        format=paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
    )
    print("Recording audio...")
    frames = []
    for i in range(0, int(44100 / 1024 * 3)):
        data = stream.read(1024)
        frames.append(data)
    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Downsampling audio...")
    audio_arr = np.frombuffer(b"".join(frames), dtype=np.int16)
    downsampled_bytes = soxr.resample(audio_arr, 44100, 8000).tobytes()

    print("Encoding/decoding audio with Codec2...")
    pkt_struct = f"{c2.samples_per_frame()}h"
    encoded_frames = []
    for i in range(0, len(downsampled_bytes), 2 * c2.samples_per_frame()):
        packet = downsampled_bytes[i : i + 2 * c2.samples_per_frame()]
        if len(packet) != 2 * c2.samples_per_frame():
            print(f"Skipping incomplete frame at index {i}")
            break
        samples = np.array(struct.unpack(pkt_struct, packet), dtype=np.int16)
        encoded_frames.append(c2.encode(samples))

    print("Sending encoded audio over serial...")
    for frame in encoded_frames:
        ser.write(frame.hex())
    ser.write(b"\n")
    ser.flush()

    print(f"Bytes sent: {len(b''.join(encoded_frames))}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttys005", help="Serial port to use")
    parser.add_argument("--key", default="space", help="Key to start/stop recording")
    args = parser.parse_args()
    port = args.port
    print(f"Sending data to {port}...")

    ser = serial.Serial(port, baudrate=115200, timeout=0)
    p_out = PyAudio()
    out_stream = p_out.open(
        format=paInt16,
        channels=1,
        rate=8000,
        output=True,
    )

    c2 = Codec2(1200)
    encoded_frame_size = c2.bits_per_frame() // 8
    expected_length = 444
    received_buffer = b""

    while True:
        if keyboard.is_pressed(args.key):
            record_and_send(ser, c2)
            while keyboard.is_pressed(args.key):
                time.sleep(0.1)

        if ser.in_waiting:
            new_data = ser.read(bytes.fromhex(ser.in_waiting))
            received_buffer += new_data
            print(
                f"Received {len(new_data)} bytes this round, total = {len(received_buffer)} bytes"
            )
            if len(received_buffer) >= expected_length:
                break
        time.sleep(0.01)

    print("Received all sent bytes")

    print("Decoding received audio...")
    decoded_frames = []

    for i in range(0, len(received_buffer), encoded_frame_size):
        frame = received_buffer[i : i + encoded_frame_size]
        if len(frame) != encoded_frame_size:
            print(f"Skipping incomplete frame at index {i}")
            break
        decoded_frames.append(c2.decode(frame))

    decoded_bytes = b"".join(decoded_frames)
    decoded_audio = np.frombuffer(decoded_bytes, dtype=np.int16)

    print("Playing received audio...")
    out_stream.write(decoded_audio.tobytes())
    out_stream.stop_stream()
    out_stream.close()
    p_out.terminate()


if __name__ == "__main__":
    main()
