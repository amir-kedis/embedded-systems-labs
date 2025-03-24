import os
import math
import time
import numpy as np
import pandas as pd
import serial
from serial.tools import list_ports

# Configuration
MAX_MEAS = 200           # Maximum number of measurements
AVG_MEAS = 25            # Number of readings to average for each measurement
SER_BAUD = 115200        # Serial baud rate
FILENAME = "calibration_data.csv"  # Output filename
RECONNECT_ATTEMPTS = 2  # Number of times to attempt reconnection
RECONNECT_DELAY = 2      # Seconds to wait between reconnection attempts

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
            arduino_ports = [p.device for p in ports if 'ACM' in p.device or 'Arduino' in p.description or 'CH340' in p.description]
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


def record_data_point(ser, num_samples=AVG_MEAS, max_retries=RECONNECT_ATTEMPTS):
    """Record data from serial port and return averaged result with retry logic."""
    readings = []
    retries = 0
    
    while len(readings) < num_samples:
        if retries >= max_retries:
            print(f"[WARNING]: Maximum retries ({max_retries}) reached. Using available data.")
            break
            
        data = ser.read(timeout=1.0)
        if not data:
            retries += 1
            print(f"[WARNING]: No data received. Retry {retries}/{max_retries}...")
            time.sleep(0.5)
            continue
            
        try:
            values = [float(x) for x in data.split(',')]
            if len(values) >= 3:  # Ensure we have at least x, y, z
                readings.append(values[:3])  # Take only the first 3 values
                print(f"[INFO]: Reading {len(readings)}/{num_samples} captured")
            else:
                print(f"[WARNING]: Invalid data format: {data}")
                retries += 1
        except (ValueError, IndexError) as e:
            print(f"[WARNING]: Data parsing error: {e} in '{data}'")
            retries += 1
    
    if not readings:
        print("[ERROR]: Failed to collect valid readings")
        return None
    
    # Calculate average of collected readings
    readings_array = np.array(readings)
    avg_reading = np.mean(readings_array, axis=0)
    
    return tuple(avg_reading)


def save_to_file(data, filename):
    """Save data to CSV file."""
    try:
        # Create DataFrame
        df = pd.DataFrame(data, columns=['ax', 'ay', 'az'])
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(filename)
        
        # Write to CSV
        df.to_csv(
            filename,
            mode='a' if file_exists else 'w',
            header=not file_exists,
            index=False
        )
        return True
    except Exception as e:
        print(f"[ERROR]: Failed to save data: {e}")
        return False


def main():
    # Initialize data storage
    all_data = []
    position_count = 0
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(FILENAME) if os.path.dirname(FILENAME) else '.', exist_ok=True)
    
    print("\n===== MPU6050 Calibration Data Collection =====")
    print("This script will collect data for ellipsoid fitting calibration.")
    print("You'll need to position the sensor in at least 8 different orientations.")
    print("Hold the sensor still in each position while measurements are taken.")
    
    # Try to connect to serial port
    ser = SerialPort(baud=SER_BAUD)
    
    try:
        while position_count < MAX_MEAS:
            print("\n" + "="*50)
            print(f"Position #{position_count + 1}")
            print("="*50)
            
            # Prepare for measurement
            print("[INFO]: Place sensor in position and keep it still.")
            user_input = input("[INPUT]: Press Enter to measure or 'q' to quit: ")
            
            if user_input.lower() == 'q':
                break
            
            # Take measurement with retry logic
            reading = None
            while reading is None:
                reading = record_data_point(ser)
                if not reading:
                    print("[ERROR]: Failed to get valid readings. Retrying...")
                    time.sleep(1)
                    continue
            
            ax, ay, az = reading
            magn = math.sqrt(ax**2 + ay**2 + az**2)
            print(f"[INFO]: Reading: X={ax:.4f}, Y={ay:.4f}, Z={az:.4f}, Magnitude={magn:.4f}")
            
            # Check if magnitude is close to 1g (expected for static accelerometer)
            if abs(magn - 1.0) > 0.15:  # Allow 15% deviation from 1g
                print("[WARNING]: Magnitude deviates significantly from 1g. Sensor may be moving or miscalibrated.")

            # Store data
            all_data.append((ax, ay, az))
            position_count += 1
            
            # Save after each successful measurement
            save_to_file([(ax, ay, az)], FILENAME)
            print(f"[INFO]: Saved position {position_count} data to {FILENAME}")
    
    except KeyboardInterrupt:
        print("\n[INFO]: Process interrupted by user.")
    finally:
        # Close serial connection
        ser.close()
        
        # Final report
        if all_data:
            print(f"\n[INFO]: Collected {position_count} position measurements.")
            print(f"[INFO]: Data saved to {os.path.abspath(FILENAME)}")
            
            # Convert to numpy array for analysis
            data_array = np.array(all_data)
            
            # Calculate statistics
            magnitudes = np.sqrt(np.sum(data_array**2, axis=1))
            print("\nData Statistics:")
            print(f"  Average magnitude: {np.mean(magnitudes):.4f}g (ideal: 1.0g)")
            print(f"  Magnitude std dev: {np.std(magnitudes):.4f}g")
            print(f"  Min/Max magnitude: {np.min(magnitudes):.4f}g / {np.max(magnitudes):.4f}g")
            
            # Check if we have enough data for calibration
            if position_count < 8:
                print("\n[WARNING]: Collected fewer than 8 positions. Ellipsoid fitting may not be accurate.")
                print("[INFO]: It's recommended to collect data from at least 8 different orientations.")
        else:
            print("[WARNING]: No data was collected.")


if __name__ == "__main__":
    main()
