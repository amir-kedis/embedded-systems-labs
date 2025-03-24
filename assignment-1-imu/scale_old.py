import numpy as np
import pandas as pd
import os

# Configuration
INPUT_FILE = "data_out.txt"  # Your input file name
OUTPUT_FILE = "calibration_data_scaled.csv"  # Output file name
SCALE_FACTOR = 16384.0  # Scale factor for +/-2g range

def main():
    try:
        # Check if input file exists
        if not os.path.exists(INPUT_FILE):
            print(f"[ERROR]: Input file '{INPUT_FILE}' not found.")
            return
        
        print(f"[INFO]: Reading data from '{INPUT_FILE}'...")
        
        # Read data from file
        # Try different approaches based on the file format
        try:
            # First attempt: Try reading as tab-separated values
            data = pd.read_csv(INPUT_FILE, sep='\t', header=None, names=['ax', 'ay', 'az'])
        except:
            try:
                # Second attempt: Try reading as space-separated values
                data = pd.read_csv(INPUT_FILE, sep=r'\s+', header=None, names=['ax', 'ay', 'az'])
            except:
                # Last attempt: Try reading as generic whitespace-separated values
                data = pd.read_csv(INPUT_FILE, delim_whitespace=True, header=None, names=['ax', 'ay', 'az'])
        
        # Check if we have data
        if data.empty:
            print("[ERROR]: Failed to read data from file.")
            return
            
        print(f"[INFO]: Successfully read {len(data)} data points.")
        
        # Scale the data
        data_scaled = data / SCALE_FACTOR
        
        # Save scaled data to output file
        data_scaled.to_csv(OUTPUT_FILE, index=False)
        
        print(f"[INFO]: Scaled data saved to '{OUTPUT_FILE}'.")
        print(f"[INFO]: Applied scaling factor: {SCALE_FACTOR}")
        
        # Show statistics
        print("\nData Statistics (Original):")
        print(f"  Min values: {data.min().values}")
        print(f"  Max values: {data.max().values}")
        print(f"  Mean values: {data.mean().values}")
        
        print("\nData Statistics (Scaled):")
        print(f"  Min values: {data_scaled.min().values}")
        print(f"  Max values: {data_scaled.max().values}")
        print(f"  Mean values: {data_scaled.mean().values}")
        
        # Calculate magnitudes
        magnitudes = np.sqrt(data_scaled['ax']**2 + data_scaled['ay']**2 + data_scaled['az']**2)
        print(f"\nMagnitude Statistics (should be close to 1.0 for static positions):")
        print(f"  Mean magnitude: {magnitudes.mean():.4f}g")
        print(f"  Min magnitude: {magnitudes.min():.4f}g")
        print(f"  Max magnitude: {magnitudes.max():.4f}g")
        print(f"  Std deviation: {magnitudes.std():.4f}g")
        
    except Exception as e:
        print(f"[ERROR]: An error occurred: {e}")

if __name__ == "__main__":
    main()