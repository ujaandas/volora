from app.VirtualSerial import VirtualSerial
import unittest


class TestVirtualSerial(unittest.TestCase):
    def setUp(self):
        self.serial = VirtualSerial()

    def test_write(self):
        data = b"Hello"
        written_bytes = self.serial.write(data)
        self.assertEqual(written_bytes, len(data))
        self.assertEqual(self.serial.in_waiting, len(data))

    def test_read(self):
        data = b"Hello"
        self.serial.write(data)
        read_data = self.serial.read(len(data))
        self.assertEqual(read_data, data)

    def test_write_and_read(self):
        data = b"Hello"
        self.serial.write(data)
        self.assertEqual(self.serial.in_waiting, len(data))
        read_data = self.serial.read(len(data))
        self.assertEqual(read_data, data)

    def test_read_timeout(self):
        data = b"Hello"
        self.serial.write(data)
        read_data = self.serial.read(len(data) + 10)
        self.assertEqual(read_data, data)

    def test_flush(self):
        data = b"Hello"
        self.serial.write(data)
        self.serial.flush()
        self.assertEqual(self.serial.in_waiting, 0)

    def test_in_waiting(self):
        data = b"Hello"
        self.serial.write(data)
        self.assertEqual(self.serial.in_waiting, len(data))
        self.serial.read(3)
        self.assertEqual(self.serial.in_waiting, 2)
