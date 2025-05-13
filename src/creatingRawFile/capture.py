import serial
import os

# Set up serial connection (make sure baudrate matches your Arduino sketch)
ser = serial.Serial('/dev/cu.usbserial-0001', baudrate=115200, timeout=1)

# File to store the received raw data
output_file = "output.raw"

# Print where it's being saved
print("Saving to:", os.path.abspath(output_file))

# Open the file in binary write mode
with open(output_file, "wb") as f:
    print("Listening on serial port... Press Ctrl+C to stop.")
    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)  # Read all available bytes
                f.write(data)
                f.flush()  # Ensure data is written to disk immediately
    except KeyboardInterrupt:
        print("\nStopped by user.")

ser.close()
print("Finished. File saved as:", output_file)
