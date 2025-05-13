import serial

ser = serial.Serial('/dev/cu.usbserial-0001', baudrate=115200, timeout=2)

print("Waiting for data...")
try:
    while True:
        line = ser.readline()
        if line:
            print("Received:", line)
except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
