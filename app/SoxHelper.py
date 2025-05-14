import numpy as np
import soxr
import struct


class SoxHelper:
    @staticmethod
    def to_raw(sound_bytes: bytes, input_rate: int, num_channels: int) -> bytes:
        samples = np.frombuffer(sound_bytes, dtype=np.int16)

        if num_channels > 1:
            samples = samples.reshape(-1, num_channels)
            samples = np.mean(samples, axis=1).astype(np.int16)

        samples = samples.astype(np.float32) / float(2**15)

        if input_rate != 8000:
            resampler = soxr.ResampleStream(input_rate, 8000, 1)
            samples = resampler.resample_chunk(samples)

        samples_int16 = np.clip(samples * (2**15), -(2**15), (2**15)).astype(np.int16)

        return samples_int16.tobytes()

    @staticmethod
    def from_raw(
        raw_bytes: bytes,
        sample_rate: int = 8000,
        num_channels: int = 1,
        bits_per_sample: int = 16,
    ) -> bytes:
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        subchunk2_size = len(raw_bytes)
        subchunk1_size = 16
        audio_format = 1
        chunk_size = 36 + subchunk2_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            chunk_size,
            b"WAVE",
            b"fmt ",
            subchunk1_size,
            audio_format,
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            subchunk2_size,
        )
        return header + raw_bytes
