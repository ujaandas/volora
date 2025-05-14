import serial
import threading
import time

# Serial port configuration
SERIAL_PORT = '/dev/cu.usbserial-0001'  # Change this to match your device
BAUD_RATE = 115200
CHUNK_SIZE = 128

# Start and end markers
START_TOKEN = "bananariptide123"
END_TOKEN = "cooliobroskiomg"

# Serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Global buffer and lock
received_buffer = ""
buffer_lock = threading.Lock()

def read_from_node():
    """Reads incoming data, detects complete messages with markers, and writes to file."""
    global received_buffer

    try:
        while True:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting).decode(errors='ignore')
                with buffer_lock:
                    received_buffer += data

                    while START_TOKEN in received_buffer and END_TOKEN in received_buffer:
                        start_idx = received_buffer.find(START_TOKEN) + len(START_TOKEN)
                        end_idx = received_buffer.find(END_TOKEN)

                        if start_idx < end_idx:
                            message = received_buffer[start_idx:end_idx].strip()

                            # Write cleaned message to file
                            with open("received_lora.raw", "wb") as f:
                                f.write(message.encode())

                            print(f"[LoRa RX] {message}")

                            # Remove the processed message from buffer
                            received_buffer = received_buffer[end_idx + len(END_TOKEN):]
            else:
                time.sleep(0.01)

    except Exception as e:
        print("Read error:", e)

def write_to_node_from_file(filename="message.raw"):
    """Reads data from a file, wraps with start/end tokens, and sends over serial."""
    try:
        with open(filename, "rb") as f:
            raw_data = f.read()

        # Wrap with tokens
        full_message = START_TOKEN.encode() + raw_data + END_TOKEN.encode()

                # Send in chunks
        for i in range(0, len(full_message), CHUNK_SIZE):
            chunk = full_message[i:i + CHUNK_SIZE] + b"\n"
            ser.write(chunk)
            #time.sleep(0.2)
            ser.flush()
            time.sleep(0.1)

        print(f"[Sent] {len(raw_data)} bytes from '{filename}'")

    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error while sending: {e}")

if __name__ == '__main__':
    print(f"Connected to LoRa node on {SERIAL_PORT}")
    print("Press Enter to send 'message.raw' (Ctrl+C to exit).")

    try:
        # Start background reader
        threading.Thread(target=read_from_node, daemon=True).start()

        # Loop to send file on user prompt
        while True:
            input("⏎  Press Enter to send the file: ")
            write_to_node_from_file("message.raw")

    finally:
        ser.close()
        print("Serial connection closed.")
