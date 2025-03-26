import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import os
from scipy.signal import butter, filtfilt, find_peaks

# Configuration
INPUT_FILE = "inclined.csv"  # Your input file with raw accelerometer data
OUTPUT_FILE = "position_results.json"  # Output file for position results
CALIBRATION_FILE = "calibration_params.json"  # Calibration parameters file
FIGURE_DIR = "position_plots"          # Directory for saving plots
UNITS_IN_MPS2 = True                  # Set to True if input data is already in m/s²
KNOWN_DISTANCE = 0.34                  # Known distance moved in meters (50cm)
LOW_PASS_FILTER = False                # Apply low-pass filter to accelerometer data
CUTOFF_FREQ = 2.0                     # Cutoff frequency for low-pass filter (Hz)
APPLY_ZUPT = False                     # Apply Zero-Velocity Update
ACC_THRESHOLD = 0.01                   # Acceleration threshold for ZUPT detection (m/s²)
WINDOW_SIZE = 5                       # Window size for ZUPT detection
SCALE_FACTOR = 0.01                   # Scale factor to apply to accelerometer data (0.01 = divide by 100)

def read_data(filename):
    """Read accelerometer data from CSV file."""
    try:
        data = pd.read_csv(filename)
        return data
    except Exception as e:
        print(f"[ERROR]: Failed to read data file: {e}")
        return None

def read_calibration_params(filename):
    """Read calibration parameters from JSON file."""
    try:
        with open(filename, 'r') as f:
            params = json.load(f)
        return params
    except Exception as e:
        print(f"[WARNING]: Failed to read calibration parameters: {e}")
        return None

def preprocess_data(data, scale_factor=1.0):
    """Apply preprocessing to the data."""
    # Create a copy of the data
    result = data.copy()
    
    # Apply scaling factor if needed
    if scale_factor != 1.0:
        print(f"[INFO]: Applying scale factor of {scale_factor} to accelerometer data")
        result['x_acc'] = result['x_acc'] * scale_factor
        result['y_acc'] = result['y_acc'] * scale_factor
        result['z_acc'] = result['z_acc'] * scale_factor
    
    return result

def apply_low_pass_filter(data, cutoff_freq=3.0, fs=None):
    """Apply low-pass filter to accelerometer data."""
    # Estimate sampling frequency if not provided
    if fs is None:
        time_diffs = np.diff(data['seconds_elapsed'])
        fs = 1.0 / np.mean(time_diffs)
    
    print(f"[INFO]: Estimated sampling frequency: {fs:.2f} Hz")
    
    # Design Butterworth low-pass filter
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(2, normal_cutoff, btype='low', analog=False)
    
    # Apply filter to each axis
    filtered_data = data.copy()
    for axis in ['x_acc', 'y_acc', 'z_acc']:
        filtered_data[axis] = filtfilt(b, a, data[axis])
    
    return filtered_data

def apply_calibration(data, cal_params):
    """Apply calibration parameters to raw accelerometer data."""
    if cal_params is None:
        print("[WARNING]: No calibration parameters provided. Using raw data.")
        return data.copy()
    
    try:
        # Extract calibration parameters
        bias = np.array(cal_params["bias"])
        transform_matrix = np.array(cal_params["transform_matrix"])
        
        # Extract raw accelerometer data
        acc_data = data[['x_acc', 'y_acc', 'z_acc']].values
        
        # If data is in m/s², convert to g for calibration
        if UNITS_IN_MPS2:
            acc_data = acc_data / 9.81
        
        # Apply calibration: A_calibrated = transform_matrix * (A_raw - bias)
        calibrated_data = np.zeros_like(acc_data)
        for i in range(len(acc_data)):
            calibrated_data[i] = np.dot(transform_matrix, (acc_data[i] - bias))
        
        # Convert back to m/s² if needed
        if UNITS_IN_MPS2:
            calibrated_data = calibrated_data * 9.81
        
        # Create a copy of the original dataframe and replace accelerometer columns
        calibrated_df = data.copy()
        calibrated_df['x_acc'] = calibrated_data[:, 0]
        calibrated_df['y_acc'] = calibrated_data[:, 1]
        calibrated_df['z_acc'] = calibrated_data[:, 2]
        
        return calibrated_df
    
    except Exception as e:
        print(f"[ERROR]: Failed to apply calibration: {e}")
        print("[WARNING]: Using raw data instead.")
        return data.copy()

def remove_gravity(data):
    """
    Remove gravity component from accelerometer data using initial stationary period.
    """
    # Use the first few samples (assumed to be stationary) to determine gravity
    initial_samples = data.iloc[:10]
    mean_acc = initial_samples[['x_acc', 'y_acc', 'z_acc']].mean().values
    
    # Calculate gravity magnitude
    gravity_magnitude = np.sqrt(np.sum(mean_acc**2))
    
    # Normalize to get gravity direction
    gravity_direction = mean_acc / gravity_magnitude
    
    print(f"[INFO]: Detected gravity: {gravity_direction} with magnitude {gravity_magnitude:.4f} m/s²")
    
    # Create a copy of the data
    result = data.copy()
    
    # Subtract gravity component from each reading
    acc_data = result[['x_acc', 'y_acc', 'z_acc']].values
    for i in range(len(acc_data)):
        # Project acceleration onto gravity direction to get gravity component
        gravity_component = np.dot(acc_data[i], gravity_direction) * gravity_direction
        
        # Subtract gravity component
        acc_data[i] = acc_data[i] - gravity_component
    
    # Update the dataframe
    result['x_acc'] = acc_data[:, 0]
    result['y_acc'] = acc_data[:, 1]
    result['z_acc'] = acc_data[:, 2]
    
    return result

def detect_stationary_periods(data, threshold=0.1, window_size=5):
    """
    Detect periods when the sensor is stationary based on acceleration variance.
    
    Args:
        data: DataFrame with accelerometer data
        threshold: Threshold for acceleration magnitude to consider stationary
        window_size: Window size for calculating variance
        
    Returns:
        Array of boolean values where True indicates stationary periods
    """
    # Calculate acceleration magnitude
    acc_mag = np.sqrt(data['x_acc']**2 + data['y_acc']**2 + data['z_acc']**2)
    
    # Calculate rolling variance
    rolling_var = pd.Series(acc_mag).rolling(window=window_size).var().fillna(0)
    
    # Detect stationary periods
    is_stationary = rolling_var < threshold
    
    return is_stationary.values

def calculate_position_with_zupt(data, acc_threshold=0.1, window_size=5):
    """
    Calculate velocity and position by integrating acceleration data with Zero-Velocity Updates.
    
    Args:
        data: DataFrame with columns 'seconds_elapsed', 'x_acc', 'y_acc', 'z_acc'
        acc_threshold: Threshold for acceleration magnitude to consider stationary
        window_size: Window size for detecting stationary periods
        
    Returns:
        DataFrame with added columns for velocity and position
    """
    # Create a copy of the input data
    result = data.copy()
    
    # If data is already in m/s², no conversion needed
    if UNITS_IN_MPS2:
        result['x_acc_mps2'] = result['x_acc']
        result['y_acc_mps2'] = result['y_acc']
        result['z_acc_mps2'] = result['z_acc']
    else:
        # Convert acceleration from g to m/s²
        g = 9.81  # gravitational acceleration in m/s²
        result['x_acc_mps2'] = result['x_acc'] * g
        result['y_acc_mps2'] = result['y_acc'] * g
        result['z_acc_mps2'] = result['z_acc'] * g
    
    # Detect stationary periods
    is_stationary = detect_stationary_periods(result, threshold=acc_threshold, window_size=window_size)
    result['is_stationary'] = is_stationary
    
    # Initialize velocity and position arrays
    time = result['seconds_elapsed'].values
    n = len(time)
    
    vx = np.zeros(n)
    vy = np.zeros(n)
    vz = np.zeros(n)
    
    px = np.zeros(n)
    py = np.zeros(n)
    pz = np.zeros(n)
    
    # Integrate acceleration to get velocity and position using trapezoidal rule
    for i in range(1, n):
        dt = time[i] - time[i-1]
        
        # Calculate velocity (v = v0 + a*dt)
        if not is_stationary[i]:
            vx[i] = vx[i-1] + 0.5 * (result['x_acc_mps2'][i-1] + result['x_acc_mps2'][i]) * dt
            vy[i] = vy[i-1] + 0.5 * (result['y_acc_mps2'][i-1] + result['y_acc_mps2'][i]) * dt
            vz[i] = vz[i-1] + 0.5 * (result['z_acc_mps2'][i-1] + result['z_acc_mps2'][i]) * dt
        else:
            # Zero-velocity update
            vx[i] = 0
            vy[i] = 0
            vz[i] = 0
        
        # Calculate position (p = p0 + v*dt)
        px[i] = px[i-1] + 0.5 * (vx[i-1] + vx[i]) * dt
        py[i] = py[i-1] + 0.5 * (vy[i-1] + vy[i]) * dt
        pz[i] = pz[i-1] + 0.5 * (vz[i-1] + vz[i]) * dt
    
    # Add velocity and position to the result DataFrame
    result['vx'] = vx
    result['vy'] = vy
    result['vz'] = vz
    
    result['px'] = px
    result['py'] = py
    result['pz'] = pz
    
    # Calculate magnitude of displacement
    result['displacement'] = np.sqrt(px**2 + py**2 + pz**2)
    
    return result

def calculate_position(data):
    """
    Calculate velocity and position by integrating acceleration data.
    
    Args:
        data: DataFrame with columns 'seconds_elapsed', 'x_acc', 'y_acc', 'z_acc'
        
    Returns:
        DataFrame with added columns for velocity and position
    """
    if APPLY_ZUPT:
        return calculate_position_with_zupt(data, acc_threshold=ACC_THRESHOLD, window_size=WINDOW_SIZE)
    
    # Create a copy of the input data
    result = data.copy()
    
    # If data is already in m/s², no conversion needed
    if UNITS_IN_MPS2:
        result['x_acc_mps2'] = result['x_acc']
        result['y_acc_mps2'] = result['y_acc']
        result['z_acc_mps2'] = result['z_acc']
    else:
        # Convert acceleration from g to m/s²
        g = 9.81  # gravitational acceleration in m/s²
        result['x_acc_mps2'] = result['x_acc'] * g
        result['y_acc_mps2'] = result['y_acc'] * g
        result['z_acc_mps2'] = result['z_acc'] * g
    
    # Initialize velocity and position arrays
    time = result['seconds_elapsed'].values
    n = len(time)
    
    vx = np.zeros(n)
    vy = np.zeros(n)
    vz = np.zeros(n)
    
    px = np.zeros(n)
    py = np.zeros(n)
    pz = np.zeros(n)
    
    # Integrate acceleration to get velocity and position using trapezoidal rule
    for i in range(1, n):
        dt = time[i] - time[i-1]
        
        # Calculate velocity (v = v0 + a*dt)
        vx[i] = vx[i-1] + 0.5 * (result['x_acc_mps2'][i-1] + result['x_acc_mps2'][i]) * dt
        vy[i] = vy[i-1] + 0.5 * (result['y_acc_mps2'][i-1] + result['y_acc_mps2'][i]) * dt
        vz[i] = vz[i-1] + 0.5 * (result['z_acc_mps2'][i-1] + result['z_acc_mps2'][i]) * dt
        
        # Calculate position (p = p0 + v*dt)
        px[i] = px[i-1] + 0.5 * (vx[i-1] + vx[i]) * dt
        py[i] = py[i-1] + 0.5 * (vy[i-1] + vy[i]) * dt
        pz[i] = pz[i-1] + 0.5 * (vz[i-1] + vz[i]) * dt
    
    # Add velocity and position to the result DataFrame
    result['vx'] = vx
    result['vy'] = vy
    result['vz'] = vz
    
    result['px'] = px
    result['py'] = py
    result['pz'] = pz
    
    # Calculate magnitude of displacement
    result['displacement'] = np.sqrt(px**2 + py**2 + pz**2)
    
    return result

def calculate_drift(position_data, known_distance=None):
    """Calculate drift metrics for position data."""
    # Get final position
    final_pos = position_data[['px', 'py', 'pz']].iloc[-1].values
    final_disp = position_data['displacement'].iloc[-1]
    
    # Calculate drift metrics
    drift_metrics = {
        "final_position": {
            "x": float(final_pos[0]),
            "y": float(final_pos[1]),
            "z": float(final_pos[2])
        },
        "final_displacement": float(final_disp),
        "drift_magnitude": float(np.linalg.norm(final_pos))
    }
    
    # If known distance is provided, calculate error
    if known_distance is not None:
        # For a back-and-forth movement, the final position should be close to zero
        # and the maximum displacement should be close to the known distance
        max_disp = position_data['displacement'].max()
        
        drift_metrics["known_distance"] = float(known_distance)
        drift_metrics["max_displacement"] = float(max_disp)
        drift_metrics["max_displacement_error"] = float(abs(max_disp - known_distance))
        drift_metrics["max_displacement_error_percent"] = float(abs(max_disp - known_distance) / known_distance * 100)
        drift_metrics["return_error"] = float(np.linalg.norm(final_pos))
        
    return drift_metrics

def create_comparison_plots(raw_data, cal_data, output_dir):
    """Create comparison plots for raw vs. calibrated data."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    time = raw_data['seconds_elapsed']
    
    # Plot 1: Acceleration Comparison
    plt.figure(figsize=(15, 10))
    
    plt.subplot(3, 1, 1)
    plt.plot(time, raw_data['x_acc'], 'r-', label='Raw')
    plt.plot(time, cal_data['x_acc'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('X Acceleration (m/s²)')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(3, 1, 2)
    plt.plot(time, raw_data['y_acc'], 'r-', label='Raw')
    plt.plot(time, cal_data['y_acc'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('Y Acceleration (m/s²)')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(3, 1, 3)
    plt.plot(time, raw_data['z_acc'], 'r-', label='Raw')
    plt.plot(time, cal_data['z_acc'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('Z Acceleration (m/s²)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'acceleration_comparison.png'), dpi=300)
    plt.close()
    
    # Plot 2: Position Comparison
    plt.figure(figsize=(15, 10))
    
    plt.subplot(3, 1, 1)
    plt.plot(time, raw_data['px'], 'r-', label='Raw')
    plt.plot(time, cal_data['px'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('X Position (m)')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(3, 1, 2)
    plt.plot(time, raw_data['py'], 'r-', label='Raw')
    plt.plot(time, cal_data['py'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('Y Position (m)')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(3, 1, 3)
    plt.plot(time, raw_data['pz'], 'r-', label='Raw')
    plt.plot(time, cal_data['pz'], 'b-', label='Calibrated')
    plt.xlabel('Time (s)')
    plt.ylabel('Z Position (m)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'position_comparison.png'), dpi=300)
    plt.close()
    
    # Plot 3: Displacement Comparison
    plt.figure(figsize=(12, 6))
    plt.plot(time, raw_data['displacement'], 'r-', label='Raw')
    plt.plot(time, cal_data['displacement'], 'b-', label='Calibrated')
    if KNOWN_DISTANCE is not None:
        plt.axhline(y=KNOWN_DISTANCE, color='g', linestyle='--', label=f'Known Distance ({KNOWN_DISTANCE}m)')
    plt.xlabel('Time (s)')
    plt.ylabel('Displacement (m)')
    plt.title('Total Displacement Comparison')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'displacement_comparison.png'), dpi=300)
    plt.close()
    
    # Plot 4: 3D Trajectory Comparison
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot raw trajectory
    ax.plot(raw_data['px'], raw_data['py'], raw_data['pz'], 'r-', label='Raw', alpha=0.7)
    ax.scatter(raw_data['px'].iloc[0], raw_data['py'].iloc[0], raw_data['pz'].iloc[0], c='g', marker='o', s=100, label='Start')
    ax.scatter(raw_data['px'].iloc[-1], raw_data['py'].iloc[-1], raw_data['pz'].iloc[-1], c='r', marker='o', s=100, label='Raw End')
    
    # Plot calibrated trajectory
    ax.plot(cal_data['px'], cal_data['py'], cal_data['pz'], 'b-', label='Calibrated', alpha=0.7)
    ax.scatter(cal_data['px'].iloc[-1], cal_data['py'].iloc[-1], cal_data['pz'].iloc[-1], c='b', marker='o', s=100, label='Calibrated End')
    
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_zlabel('Z Position (m)')
    ax.set_title('3D Trajectory Comparison')
    ax.legend()
    
    # Set equal aspect ratio
    max_range = np.array([
        max(raw_data['px'].max(), cal_data['px'].max()) - min(raw_data['px'].min(), cal_data['px'].min()),
        max(raw_data['py'].max(), cal_data['py'].max()) - min(raw_data['py'].min(), cal_data['py'].min()),
        max(raw_data['pz'].max(), cal_data['pz'].max()) - min(raw_data['pz'].min(), cal_data['pz'].min())
    ]).max() / 2.0
    
    mid_x = (max(raw_data['px'].max(), cal_data['px'].max()) + min(raw_data['px'].min(), cal_data['px'].min())) / 2
    mid_y = (max(raw_data['py'].max(), cal_data['py'].max()) + min(raw_data['py'].min(), cal_data['py'].min())) / 2
    mid_z = (max(raw_data['pz'].max(), cal_data['pz'].max()) + min(raw_data['pz'].min(), cal_data['pz'].min())) / 2
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3d_trajectory_comparison.png'), dpi=300)
    plt.close()
    
    # Plot 5: 2D Trajectory Comparison (Top View)
    plt.figure(figsize=(10, 10))
    plt.plot(raw_data['px'], raw_data['py'], 'r-', label='Raw', alpha=0.7)
    plt.plot(cal_data['px'], cal_data['py'], 'b-', label='Calibrated', alpha=0.7)
    
    plt.scatter(0, 0, c='g', marker='o', s=100, label='Start')
    plt.scatter(raw_data['px'].iloc[-1], raw_data['py'].iloc[-1], c='r', marker='o', s=100, label='Raw End')
    plt.scatter(cal_data['px'].iloc[-1], cal_data['py'].iloc[-1], c='b', marker='o', s=100, label='Calibrated End')
    
    plt.xlabel('X Position (m)')
    plt.ylabel('Y Position (m)')
    plt.title('2D Trajectory Comparison (Top View)')
    plt.grid(True)
    plt.axis('equal')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2d_trajectory_comparison.png'), dpi=300)
    plt.close()
    
    # Plot 6: Stationary periods (if ZUPT is applied)
    if APPLY_ZUPT and 'is_stationary' in raw_data.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(time, raw_data['is_stationary'].astype(int), 'r-', label='Raw')
        plt.plot(time, cal_data['is_stationary'].astype(int), 'b-', label='Calibrated')
        plt.xlabel('Time (s)')
        plt.ylabel('Is Stationary')
        plt.title('Detected Stationary Periods')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'stationary_periods.png'), dpi=300)
        plt.close()

def save_results(raw_metrics, cal_metrics, filename):
    """Save position calculation results to a JSON file."""
    try:
        # Calculate improvement metrics
        improvement = {
            "return_error_reduction": float(raw_metrics["return_error"] - cal_metrics["return_error"]),
            "return_error_reduction_percent": float((raw_metrics["return_error"] - cal_metrics["return_error"]) / raw_metrics["return_error"] * 100) if raw_metrics["return_error"] > 0 else 0,
            "max_displacement_error_reduction": float(raw_metrics["max_displacement_error"] - cal_metrics["max_displacement_error"]),
            "max_displacement_error_reduction_percent": float((raw_metrics["max_displacement_error"] - cal_metrics["max_displacement_error"]) / raw_metrics["max_displacement_error"] * 100) if raw_metrics["max_displacement_error"] > 0 else 0
        }
        
        # Combine results
        results = {
            "raw_data_metrics": raw_metrics,
            "calibrated_data_metrics": cal_metrics,
            "improvement": improvement
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"[INFO]: Results saved to {filename}")
        return True
    except Exception as e:
        print(f"[ERROR]: Failed to save results: {e}")
        return False

def main():
    # Create output directory
    if not os.path.exists(FIGURE_DIR):
        os.makedirs(FIGURE_DIR)
    
    # Read accelerometer data
    print(f"[INFO]: Reading data from {INPUT_FILE}...")
    data = read_data(INPUT_FILE)
    if data is None:
        return
    
    print(f"[INFO]: Loaded {len(data)} data points spanning {data['seconds_elapsed'].iloc[-1]:.2f} seconds.")
    
    # Preprocess data (apply scaling factor)
    data = preprocess_data(data, scale_factor=SCALE_FACTOR)
    
    # Make a copy of the raw data
    raw_data = data.copy()
    
    # Apply low-pass filter if enabled
    if LOW_PASS_FILTER:
        print("[INFO]: Applying low-pass filter...")
        raw_data = apply_low_pass_filter(raw_data, cutoff_freq=CUTOFF_FREQ)
    
    # Read calibration parameters
    cal_params = read_calibration_params(CALIBRATION_FILE)
    if cal_params:
        print("[INFO]: Calibration parameters loaded successfully.")
    else:
        print("[WARNING]: No calibration parameters found. Will only process raw data.")
    
    # Apply calibration to create calibrated dataset
    cal_data = apply_calibration(raw_data.copy(), cal_params) if cal_params else None
    
    # Process raw data
    print("[INFO]: Processing raw data...")
    raw_data_no_gravity = remove_gravity(raw_data)
    raw_position_data = calculate_position(raw_data_no_gravity)
    
    # Process calibrated data if available
    if cal_data is not None:
        print("[INFO]: Processing calibrated data...")
        cal_data_no_gravity = remove_gravity(cal_data)
        cal_position_data = calculate_position(cal_data_no_gravity)
    else:
        cal_position_data = None
    
    # Calculate drift metrics
    raw_metrics = calculate_drift(raw_position_data, known_distance=KNOWN_DISTANCE)
    cal_metrics = calculate_drift(cal_position_data, known_distance=KNOWN_DISTANCE) if cal_position_data is not None else None
    
    # Create comparison plots if both datasets are available
    if cal_position_data is not None:
        print("[INFO]: Creating comparison plots...")
        create_comparison_plots(raw_position_data, cal_position_data, FIGURE_DIR)
    
    # Save results
    if cal_metrics is not None:
        save_results(raw_metrics, cal_metrics, OUTPUT_FILE)
    
    # Print summary
    print("\n=== Position Calculation Results ===")
    print("\nRaw Data Metrics:")
    print(f"  Final position (x, y, z): ({raw_metrics['final_position']['x']:.4f}, {raw_metrics['final_position']['y']:.4f}, {raw_metrics['final_position']['z']:.4f}) meters")
    print(f"  Final displacement: {raw_metrics['final_displacement']:.4f} meters")
    print(f"  Return error: {raw_metrics['return_error']:.4f} meters")
    if 'max_displacement' in raw_metrics:
        print(f"  Maximum displacement: {raw_metrics['max_displacement']:.4f} meters")
        print(f"  Maximum displacement error: {raw_metrics['max_displacement_error']:.4f} meters ({raw_metrics['max_displacement_error_percent']:.2f}%)")
    
    if cal_metrics is not None:
        print("\nCalibrated Data Metrics:")
        print(f"  Final position (x, y, z): ({cal_metrics['final_position']['x']:.4f}, {cal_metrics['final_position']['y']:.4f}, {cal_metrics['final_position']['z']:.4f}) meters")
        print(f"  Final displacement: {cal_metrics['final_displacement']:.4f} meters")
        print(f"  Return error: {cal_metrics['return_error']:.4f} meters")
        if 'max_displacement' in cal_metrics:
            print(f"  Maximum displacement: {cal_metrics['max_displacement']:.4f} meters")
            print(f"  Maximum displacement error: {cal_metrics['max_displacement_error']:.4f} meters ({cal_metrics['max_displacement_error_percent']:.2f}%)")
        
        # Print improvement
        return_error_reduction = raw_metrics['return_error'] - cal_metrics['return_error']
        return_error_reduction_percent = (return_error_reduction / raw_metrics['return_error'] * 100) if raw_metrics['return_error'] > 0 else 0
        
        print("\nImprovement with Calibration:")
        print(f"  Return error reduction: {return_error_reduction:.4f} meters ({return_error_reduction_percent:.2f}%)")
        
        if 'max_displacement_error' in raw_metrics and 'max_displacement_error' in cal_metrics:
            max_disp_error_reduction = raw_metrics['max_displacement_error'] - cal_metrics['max_displacement_error']
            max_disp_error_reduction_percent = (max_disp_error_reduction / raw_metrics['max_displacement_error'] * 100) if raw_metrics['max_displacement_error'] > 0 else 0
            print(f"  Maximum displacement error reduction: {max_disp_error_reduction:.4f} meters ({max_disp_error_reduction_percent:.2f}%)")
    
    print(f"\nPlots saved to {FIGURE_DIR} directory")
    print(f"Detailed results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()