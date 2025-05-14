import time
import serial
import keyboard
import pyaudio
import numpy as np
import soxr
import pycodec2
import struct


def main():
    try:
        ser = serial.Serial(port="/dev/ttys008", baudrate=115200, timeout=0)
    except Exception as e:
        print("Error opening serial port:", e)
        return

    p1 = pyaudio.PyAudio()

    c2 = pycodec2.Codec2(1200)
    INT16_BYTE_SIZE = 2
    PACKET_SIZE = c2.samples_per_frame() * INT16_BYTE_SIZE
    STRUCT_FORMAT = "{}h".format(c2.samples_per_frame())

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

        downsampled_audio = soxr.resample(
            audio_array,
            input_rate,
            output_rate,
        )

        return downsampled_audio.tobytes()

    def encode_audio(audio_data):
        print("Encoding audio with Codec2...")
        encoded_frames = []

        for i in range(0, len(audio_data), PACKET_SIZE):
            packet = audio_data[i : i + PACKET_SIZE]
            if len(packet) != PACKET_SIZE:
                break
            samples = np.array(struct.unpack(STRUCT_FORMAT, packet), dtype=np.int16)
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

                print("Sending encoded audio data...")
                ser.write(encoded_data)

            if ser.in_waiting > 0:
                print("Receiving encoded audio data from serial...")
                incoming_encoded_data = ser.read(ser.in_waiting)

                decoded_audio = decode_audio(incoming_encoded_data)
                print(f"Decoded audio to {len(decoded_audio)} bytes.")

                playback(decoded_audio, rate=8000)

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()
        p1.terminate()


if __name__ == "__main__":
    main()
