from pyaudio import PyAudio, paInt16


class AudioHelper:
    def __init__(self):
        self.chunk_size = 1024
        self.format = paInt16  # each sample is 16 bits, ie; 2 bytes
        self.channels = 1
        self.rate = 44100

        self.audio = PyAudio()
        self.buf = bytearray()

        self.stream: PyAudio = None

    def start_stream(self):
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

    def stop_stream(self):
        self.stream.stop_stream()
        self.stream.close()

    def clear_buffer(self):
        self.buf.clear()

    def record(self, time: int):
        self.clear_buffer()
        self.start_stream()

        for _ in range(0, int(self.rate / self.chunk_size * time)):
            data = self.stream.read(self.chunk_size)
            self.buf.extend(data)

        self.stop_stream()

    def listen(self):
        self.start_stream()
        data = self.stream.read(self.chunk_size)
        self.stop_stream()
        return data
