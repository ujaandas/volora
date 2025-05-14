import queue


class VirtualSerial:
    def __init__(self, *args, **kwargs):
        self._buffer = queue.Queue()
        self.is_open = True

    def write(self, data: bytes) -> int:
        for b in data:
            self._buffer.put(b)
        return len(data)

    def flush(self):
        self._buffer.queue.clear()

    def read(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            try:
                b = self._buffer.get(timeout=0.1)
                result.append(b)
            except queue.Empty:
                break
        return bytes(result)

    @property
    def in_waiting(self) -> int:
        return self._buffer.qsize()

    def close(self):
        self.is_open = False
