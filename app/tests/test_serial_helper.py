from app.SerialHelper import SerialHelper
from app.VirtualSerial import VirtualSerial
import unittest
from unittest.mock import patch
from io import StringIO
import sys


class TestSerialHelper(unittest.TestCase):
    def setUp(self):
        self.port = "COM_TEST"
        self.baudrate = 9600
        self.serial_helper = SerialHelper(self.port, self.baudrate)

    def test_init(self):
        self.assertEqual(self.serial_helper.port, self.port)
        self.assertEqual(self.serial_helper.baudrate, self.baudrate)
        self.assertIsNone(self.serial_helper.serial)

    @patch("app.SerialHelper.Serial", new=VirtualSerial)
    def test_connect_success(self):
        self.serial_helper.connect()
        self.assertIsInstance(self.serial_helper.serial, VirtualSerial)
        self.assertTrue(self.serial_helper.serial.is_open)

    @patch("app.SerialHelper.Serial", side_effect=Exception("Connection error"))
    def test_connect_failure(self, mock_serial):
        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.connect()
        sys.stdout = sys.__stdout__
        self.assertIsNone(self.serial_helper.serial)
        self.assertIn("Failed to connect", captured_output.getvalue())

    def test_disconnect_when_open(self):
        vs = VirtualSerial()
        vs.is_open = True
        self.serial_helper.serial = vs

        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.disconnect()
        sys.stdout = sys.__stdout__

        self.assertFalse(vs.is_open)
        self.assertIn("Disconnected from", captured_output.getvalue())

    def test_disconnect_when_not_open(self):
        self.serial_helper.serial = None
        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.disconnect()
        sys.stdout = sys.__stdout__
        self.assertIn("Serial port is not open", captured_output.getvalue())

        vs = VirtualSerial()
        vs.is_open = False
        self.serial_helper.serial = vs
        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.disconnect()
        sys.stdout = sys.__stdout__
        self.assertIn("Serial port is not open", captured_output.getvalue())

    def test_send_bytes_when_connected(self):
        vs = VirtualSerial()
        vs.is_open = True
        self.serial_helper.serial = vs
        data = b"Hello"
        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.send_bytes(data)
        sys.stdout = sys.__stdout__

        read_back = vs.read(len(data))
        self.assertEqual(read_back, data)
        self.assertIn("Sent:", captured_output.getvalue())

    def test_send_bytes_when_not_connected(self):
        self.serial_helper.serial = None
        captured_output = StringIO()
        sys.stdout = captured_output
        self.serial_helper.send_bytes(b"Hello")
        sys.stdout = sys.__stdout__
        self.assertIn("Serial port is not open", captured_output.getvalue())

    def test_read_bytes_when_connected(self):
        vs = VirtualSerial()
        vs.is_open = True
        self.serial_helper.serial = vs
        dummy_data = b"Response"
        vs.write(dummy_data)
        result = self.serial_helper.read_bytes(len(dummy_data))
        self.assertEqual(result, dummy_data)

    def test_read_bytes_when_not_connected(self):
        self.serial_helper.serial = None
        captured_output = StringIO()
        sys.stdout = captured_output
        result = self.serial_helper.read_bytes(8)
        sys.stdout = sys.__stdout__
        self.assertIn("Serial port is not open", captured_output.getvalue())
        self.assertEqual(result, b"")

    @patch("app.SerialHelper.Serial", new=VirtualSerial)
    def test_context_manager(self):
        with SerialHelper(self.port, self.baudrate) as helper:
            self.assertIsInstance(helper.serial, VirtualSerial)
            self.assertTrue(helper.serial.is_open)
        self.assertFalse(helper.serial.is_open)
