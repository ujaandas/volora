import unittest
from app.AudioHelper import AudioHelper


class TestAudioHelper(unittest.TestCase):
    def setUp(self):
        self.audio_helper = AudioHelper()

    def test_init(self):
        self.assertEqual(self.audio_helper.chunk_size, 1024)
        self.assertEqual(self.audio_helper.format, 8)
        self.assertEqual(self.audio_helper.channels, 1)
        self.assertEqual(self.audio_helper.rate, 44100)

    def test_start_stream(self):
        self.audio_helper._start_stream()
        self.assertIsNotNone(self.audio_helper.stream)

    def test_stop_stream(self):
        self.audio_helper._start_stream()
        stream = self.audio_helper.stream
        self.audio_helper._stop_stream()
        self.assertRaises(OSError, lambda: stream.is_active())

    def test_stop_inactive_stream(self):
        self.assertRaises(AttributeError, lambda: self.audio_helper._stop_stream())
        self.assertIsNone(self.audio_helper.stream)

    def test_start_stream_twice(self):
        self.audio_helper._start_stream()
        stream = self.audio_helper.stream
        self.audio_helper._start_stream()
        self.assertNotEqual(self.audio_helper.stream, stream)

    def test_buf_after_record(self):
        self.audio_helper.record(1)
        self.assertGreater(len(self.audio_helper.buf), 0)

    def test_clear_buf(self):
        self.audio_helper.record(1)
        self.audio_helper._clear_buffer()
        self.assertEqual(len(self.audio_helper.buf), 0)

    def test_buf_len(self):
        self.audio_helper.record(1)
        self.assertGreater(len(self.audio_helper.buf), 0)
        self.assertEqual(
            len(self.audio_helper.buf),
            self.audio_helper.chunk_size
            * (self.audio_helper.rate // self.audio_helper.chunk_size)
            * 1
            * 2,
        )

    def test_play(self):
        recorded = self.audio_helper.record(1)
        try:
            self.audio_helper.play(recorded)
        except Exception as e:
            self.fail(f"play method raised an exception: {e}")
