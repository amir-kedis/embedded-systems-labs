import os
import math
import time
import datetime
import numpy as np
import pandas as pd
import serial
from serial.tools import list_ports

# Configuration
MAX_MEAS = 200  # Maximum number of measurements
SER_BAUD = 115200  # Serial baud rate
FILENAME = "imu_raw_data.csv"  # Output filename
RECONNECT_ATTEMPTS = 2  # Number of times to attempt reconnection
RECONNECT_DELAY = 2  # Seconds to wait between reconnection attempts


class SerialPort:
    """Create and read data from a serial port with improved error handling."""

    def __init__(self, port=None, baud=115200):
        """Create and read serial data.

        Args:
            port (str): Serial port name. If None, auto-detect.
            baud (int): Serial baud rate, default 115200.
        """
        self.port = port
        self.baud = baud
        self.ser = None
        self.connect()

    def connect(self):
        """Connect to the serial port with auto-detection if needed."""
        if self.ser and self.ser.is_open:
            return True

        # Auto-detect port if not specified
        if not self.port:
            ports = list_ports.comports()
            arduino_ports = [
                p.device
                for p in ports
                if "ACM" in p.device
                or "Arduino" in p.description
                or "CH340" in p.description
            ]
            if not arduino_ports:
                print("[ERROR]: No Arduino device found. Available ports:")
                for p in ports:
                    print(f"  - {p.device}: {p.description}")
                return False
            self.port = arduino_ports[0]
            print(f"[INFO]: Auto-detected Arduino on port {self.port}")

        try:
            self.ser = serial.Serial(
                self.port,
                self.baud,
                timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
            time.sleep(2)  # Wait for Arduino to reset after connection
            self.ser.flushInput()
            self.ser.flushOutput()
            print(f"[INFO]: Connected to {self.port} at {self.baud} baud")
            return True
        except serial.SerialException as e:
            print(f"[ERROR]: Failed to connect to {self.port}: {e}")
            return False

    def read(self, clean_end=True, timeout=1.0):
        """Read and decode data string from serial port with timeout.

        Args:
            clean_end (bool): Strip '\\r' and '\\n' characters from string.
            timeout (float): Maximum time to wait for data in seconds.

        Returns:
            str: utf-8 decoded message or None if timeout/error.
        """
        if not self.ser or not self.ser.is_open:
            if not self.connect():
                return None

        try:
            self.ser.timeout = timeout
            bytesToRead = self.ser.readline()
            if not bytesToRead:
                return None

            decodedMsg = bytesToRead.decode("utf-8")
            if clean_end:
                decodedMsg = decodedMsg.rstrip()
            return decodedMsg
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[WARNING]: Serial read error: {e}")
            # Try to reconnect
            self.connect()
            return None

    def close(self):
        """Close serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[INFO]: Serial connection closed")


def record_raw_data(ser, duration=10, max_retries=RECONNECT_ATTEMPTS):
    """Record raw data from serial port for specified duration with timestamps."""
    readings = []
    retries = 0
    start_time = time.time()
    end_time = start_time + duration

    print(f"[INFO]: Recording raw data for {duration} seconds...")

    while time.time() < end_time:
        if retries >= max_retries:
            print(f"[WARNING]: Maximum retries ({max_retries}) reached.")
            break

        data = ser.read(timeout=0.1)  # Short timeout to capture data frequently

        if not data:
            retries += 1
            continue

        try:
            values = [float(x) for x in data.split(",")]
            if len(values) >= 3:  
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ]
                reading = (timestamp, values[0], values[1], values[2])
                readings.append(reading)

                # Save each reading immediately to avoid data loss
                save_to_file([reading], FILENAME)

                # Print progress every second
                if len(readings) % 10 == 0:
                    print(f"[INFO]: Captured {len(readings)} readings so far...")
            else:
                print(f"[WARNING]: Invalid data format: {data}")
        except (ValueError, IndexError) as e:
            print(f"[WARNING]: Data parsing error: {e} in '{data}'")
            retries += 1

    print(f"[INFO]: Recorded {len(readings)} raw readings")
    return readings


def save_to_file(data, filename):
    """Save data to CSV file."""
    try:
        # Create DataFrame
        df = pd.DataFrame(data, columns=["timestamp", "ax", "ay", "az"])

        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(filename)

        # Write to CSV
        df.to_csv(
            filename,
            mode="a" if file_exists else "w",
            header=not file_exists,
            index=False,
        )
        return True
    except Exception as e:
        print(f"[ERROR]: Failed to save data: {e}")
        return False


def main():
    # Create output directory if it doesn't exist
    os.makedirs(
        os.path.dirname(FILENAME) if os.path.dirname(FILENAME) else ".", exist_ok=True
    )

    print("\n===== IMU Raw Data Collection =====")
    print("This script will collect raw IMU data with timestamps.")
    print("Data will be saved to CSV as it's collected.")

    # Try to connect to serial port
    ser = SerialPort(baud=SER_BAUD)

    if not ser.ser:
        print("[ERROR]: Failed to initialize serial connection.")
        return

    try:
        while True:
            print("\n" + "=" * 50)
            print("IMU Data Recording")
            print("=" * 50)

            # Get recording duration from user
            try:
                duration = float(
                    input(
                        "[INPUT]: Enter recording duration in seconds (or 0 to quit): "
                    )
                )
                if duration <= 0:
                    break
            except ValueError:
                print("[ERROR]: Please enter a valid number.")
                continue

            # Record raw data
            readings = record_raw_data(ser, duration=duration)

            if not readings:
                print("[WARNING]: No data was collected in this session.")
            else:
                print(f"[INFO]: Successfully recorded {len(readings)} data points.")
                print(f"[INFO]: Data saved to {os.path.abspath(FILENAME)}")

                # Show a sample of the data
                if len(readings) > 0:
                    print("\nSample data:")
                    for i in range(min(3, len(readings))):
                        timestamp, x, y, z = readings[i]
                        print(f"  {timestamp}: X={x:.4f}, Y={y:.4f}, Z={z:.4f}")

            # Ask if user wants to continue
            if input("\n[INPUT]: Record more data? (y/n): ").lower() != "y":
                break

    except KeyboardInterrupt:
        print("\n[INFO]: Process interrupted by user.")
    finally:
        # Close serial connection
        ser.close()

        if os.path.isfile(FILENAME):
            print(f"\n[INFO]: All data saved to {os.path.abspath(FILENAME)}")

            # Provide basic statistics if data was collected
            try:
                df = pd.read_csv(FILENAME)
                if not df.empty:
                    print("\nData Statistics:")
                    print(f"  Total readings: {len(df)}")
                    print(
                        f"  Time span: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}"
                    )
                    print(f"  X range: {df['x'].min():.4f} to {df['x'].max():.4f}")
                    print(f"  Y range: {df['y'].min():.4f} to {df['y'].max():.4f}")
                    print(f"  Z range: {df['z'].min():.4f} to {df['z'].max():.4f}")
            except Exception as e:
                print(f"[WARNING]: Could not analyze data: {e}")
        else:
            print("[WARNING]: No data was collected.")


if __name__ == "__main__":
    main()
