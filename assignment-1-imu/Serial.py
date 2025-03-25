import serial
import time
import sys
import pandas as pd
from scipy.constants import g

# Check if the user provided an argument (axis)
if len(sys.argv) != 2 or sys.argv[1] not in ['x', 'y', 'z']:
    print("Usage: python script.py <axis>")
    print("<axis> should be one of 'x', 'y', or 'z'.")
    sys.exit(1)

# Get the axis to filter (x, y, or z) for the filename
axis = sys.argv[1]

# Set up the serial connection (adjust the COM port accordingly)
arduino = serial.Serial('COM6', 115200)  # Replace with your Arduino port
time.sleep(2)  # Give the connection time to establish

# Create an empty list to store data
data_list = []
read_count = 0

while read_count < 200:
    # Read data from the serial port
    if arduino.in_waiting > 0:
        data = arduino.readline().decode('utf-8').strip()
        
        # Parse the data assuming it's in CSV format: Timestamp,aX,aY,aZ,gX,gY,gZ
        values = data.split(',')
        if len(values) >= 7:  # Ensure we have all the data
            timestamp = values[0]
            sensor_x = values[1]
            sensor_y = values[2]
            sensor_z = values[3]
            gyro_x = values[4]
            gyro_y = values[5]
            gyro_z = values[6]
            
            
        
            # Append data to the list
            data_list.append([timestamp, sensor_x, sensor_y, sensor_z, gyro_x, gyro_y, gyro_z])
            read_count += 1

            # Print the received data (optional)
            print(f"#{read_count}\tReceived from Arduino: {data}")

# Convert the list to a Pandas DataFrame
df = pd.DataFrame(data_list, columns=["seconds_elapsed", "x_acc", "y_acc", "z_acc", "x_gyro", "y_gyro", "z_gyro"])

# Save the DataFrame to a CSV file
filename = f"{axis}_axis.csv"
df.to_csv(filename, index=False)

print(f"Data saved to {filename} ({read_count} reads)")
