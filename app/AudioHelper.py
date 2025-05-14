from pyaudio import PyAudio, paInt16


class AudioHelper:
    def __init__(self):
        self.chunk_size = 1024
        self.format = paInt16
        self.channels = 1
        self.rate = 44100
        self.pyaudio = None
        self.stream = None
        self.buf = bytearray()

    def start_stream(self, input=True, output=False):
        self.pyaudio = PyAudio()
        self.stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=input,
            output=output,
            frames_per_buffer=self.chunk_size,
        )

    def stop_stream(self):
        if self.stream is None:
            raise AttributeError(
                "Stream is not started. Please call _start_stream first."
            )
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        self.stream = None
        self.pyaudio = None

    def clear_buf(self):
        self.buf.clear()

    def record(self, time: int) -> bytes:
        self.start_stream(input=True, output=False)
        self.clear_buf()
        iterations = self.rate // self.chunk_size * time
        for _ in range(iterations):
            data = self.stream.read(self.chunk_size)
            self.buf.extend(data)
        self.stop_stream()
        return bytes(self.buf)

    def play(self, audio_data: bytes):
        self.start_stream(input=False, output=True)
        self.stream.write(audio_data)
        self.stop_stream()
