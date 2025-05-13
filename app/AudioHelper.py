from pyaudio import PyAudio, paInt16


class AudioHelper:
    def __init__(self):
        self.chunk_size = 1024
        self.format = paInt16  # each sample is 16 bits, ie; 2 bytes
        self.channels = 1
        self.rate = 44100

        self.pyaudio = None
        self.stream = None
        self.buf = bytearray()

    def _start_stream(self):
        self.pyaudio = PyAudio()
        self.stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

    def _stop_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        self.stream = None
        self.pyaudio = None

    def _clear_buffer(self):
        self.buf.clear()

    def record(self, time: int):
        self._start_stream()
        if self.stream is None:
            raise AttributeError(
                "Stream is not started. Please call _start_stream first."
            )
        self._clear_buffer()
        for _ in range(0, int(self.rate / self.chunk_size * time)):
            data = self.stream.read(self.chunk_size)
            self.buf.extend(data)
        self._stop_stream()

    def listen(self):
        self._start_stream()
        if self.stream is None:
            raise AttributeError(
                "Stream is not started. Please call _start_stream first."
            )
        data = self.stream.read(self.chunk_size)
        self._stop_stream()
        return data
