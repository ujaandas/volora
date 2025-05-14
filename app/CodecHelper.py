import struct
import numpy as np
import pycodec2


class Codec2Helper:
    def __init__(self, bitrate=1200):
        self.codec = pycodec2.Codec2(bitrate)
        self.INT16_BYTE_SIZE = 2
        self.samples_per_frame = self.codec.samples_per_frame()
        self.PACKET_SIZE = self.samples_per_frame * self.INT16_BYTE_SIZE
        self.STRUCT_FORMAT = "{}h".format(self.samples_per_frame)

    def encode(self, sound_bytes: bytes):
        encoded_frames = []
        total_bytes = len(sound_bytes)
        num_complete_frames = total_bytes // self.PACKET_SIZE
        remainder = total_bytes % self.PACKET_SIZE

        for i in range(num_complete_frames):
            start = i * self.PACKET_SIZE
            packet = sound_bytes[start : start + self.PACKET_SIZE]
            samples = np.array(
                struct.unpack(self.STRUCT_FORMAT, packet), dtype=np.int16
            )
            encoded = self.codec.encode(samples)
            encoded_frames.append(encoded)

        if remainder:
            packet = sound_bytes[num_complete_frames * self.PACKET_SIZE :]
            packet += b"\x00" * (self.PACKET_SIZE - len(packet))
            samples = np.array(
                struct.unpack(self.STRUCT_FORMAT, packet), dtype=np.int16
            )
            encoded = self.codec.encode(samples)
            encoded_frames.append(encoded)

        return encoded_frames

    def decode(self, encoded_frames):
        decoded_bytes = bytearray()

        for encoded in encoded_frames:
            decoded_samples = self.codec.decode(encoded)
            packet = struct.pack(self.STRUCT_FORMAT, *decoded_samples)
            decoded_bytes.extend(packet)

        return bytes(decoded_bytes)
