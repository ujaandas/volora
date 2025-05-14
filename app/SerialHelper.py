from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_ONE


class SerialHelper:
    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None

    def connect(self):
        try:
            self.serial = Serial(
                self.port,
                self.baudrate,
                timeout=1,
                bytesize=EIGHTBITS,
                parity=PARITY_NONE,
                stopbits=STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
            )
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        except Exception as e:
            print(f"Failed to connect: {e}")

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            print(f"Disconnected from {self.port}.")
        else:
            print("Serial port is not open.")

    def send_bytes(self, data: bytes):
        if self.serial and self.serial.is_open:
            self.serial.write(data)
            print(f"Sent: {data}")
        else:
            print("Serial port is not open.")

    def read_bytes(self, size: int) -> bytes:
        if self.serial and self.serial.is_open:
            data = self.serial.read(size)
            print(f"Received: {data}")
            return data
        else:
            print("Serial port is not open.")
            return b""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
