import time
import keyboard
from VirtualSerial import VirtualSerial
from SerialHelper import SerialHelper
from AudioHelper import AudioHelper
from SoxHelper import SoxHelper
from CodecHelper import Codec2Helper


def main():
    print("hello")
    audio = AudioHelper()
    codec = Codec2Helper()
    vs = VirtualSerial()
    vs.is_open = True
    serial_helper = SerialHelper(vs)
    audio.rate = 44100
    audio.start_stream()

    while True:
        try:
            if keyboard.is_pressed("space"):
                sound = audio.record(3)
                raw = SoxHelper.to_raw(sound, input_rate=44100, num_channels=1)
                encoded_frames = codec.encode(raw)
                send_data = b"".join(encoded_frames)
                serial_helper.send_bytes(send_data)
                time.sleep(0.1)
            else:
                ENCODED_FRAME_SIZE = 10
                received = serial_helper.read_bytes(ENCODED_FRAME_SIZE)
                if received:
                    decoded_bytes = codec.decode([received])
                    audio.rate = 8000
                    audio.play(decoded_bytes)
                time.sleep(0.1)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
