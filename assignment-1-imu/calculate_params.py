import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import linalg
import json
import os

# Configuration
INPUT_FILE = "output.csv"  # Your input file with scaled data
OUTPUT_FILE = "calibration_params.json"     # Output file for calibration parameters
FIGURE_DIR = "calibration_plots"            # Directory for saving plots

def read_data(filename):
    """Read accelerometer data from CSV file."""
    try:
        data = pd.read_csv(filename)
        return data
    except Exception as e:
        print(f"[ERROR]: Failed to read data file: {e}")
        return None

def fit_ellipsoid(X, Y, Z):
    """
    Fit an ellipsoid to the provided 3D points using least squares.
    Returns the center, radii, and rotation matrix of the ellipsoid.
    """
    # Formulate and solve the least squares problem ||Ax - b ||^2
    D = np.column_stack([X**2, Y**2, Z**2, 2*X*Y, 2*X*Z, 2*Y*Z, 2*X, 2*Y, 2*Z])
    b = np.ones_like(X)
    
    # Solve the normal equation
    u = np.linalg.lstsq(D, b, rcond=None)[0]
    
    # Extract parameters
    A = np.array([
        [u[0], u[3], u[4], u[6]],
        [u[3], u[1], u[5], u[7]],
        [u[4], u[5], u[2], u[8]],
        [u[6], u[7], u[8], -1]
    ])
    
    # Find the center of the ellipsoid
    center = np.linalg.solve(-A[:3, :3], A[:3, 3])
    
    # Form the algebraic form of the ellipsoid
    T = np.eye(4)
    T[:3, 3] = center
    R = T.dot(A).dot(T.T)
    
    # Extract the radii from the diagonal elements
    evals, evecs = np.linalg.eig(R[:3, :3] / -R[3, 3])
    radii = 1.0 / np.sqrt(evals)
    
    return center, radii, evecs

def calibrate_accelerometer(data):
    """
    Calibrate accelerometer data using ellipsoid fitting.
    Returns calibration parameters and calibrated data.
    """
    # Extract accelerometer data
    X = data['ax'].values
    Y = data['ay'].values
    Z = data['az'].values
    
    # Fit ellipsoid to the data
    center, radii, evecs = fit_ellipsoid(X, Y, Z)
    
    # Create transformation matrix
    # The calibration formula is: A_calibrated = Scale * (A_raw - Bias)
    bias = center
    
    # The scale matrix combines the rotation and scaling to transform the ellipsoid to a sphere
    rotation_matrix = evecs
    scaling_matrix = np.diag(1.0 / radii)
    transform_matrix = rotation_matrix.dot(scaling_matrix)
    
    # Apply calibration to the data
    data_points = np.column_stack([X, Y, Z])
    centered_data = data_points - bias
    calibrated_data = np.dot(centered_data, transform_matrix.T)
    
    # Create a DataFrame with calibrated data
    calibrated_df = pd.DataFrame({
        'ax': calibrated_data[:, 0],
        'ay': calibrated_data[:, 1],
        'az': calibrated_data[:, 2]
    })
    
    # Calculate magnitudes
    raw_magnitudes = np.sqrt(X**2 + Y**2 + Z**2)
    cal_magnitudes = np.sqrt(calibrated_df['ax']**2 + calibrated_df['ay']**2 + calibrated_df['az']**2)
    
    # Print statistics
    print("\nCalibration Results:")
    print(f"Bias (offset): [{bias[0]:.6f}, {bias[1]:.6f}, {bias[2]:.6f}]")
    print(f"Radii: [{radii[0]:.6f}, {radii[1]:.6f}, {radii[2]:.6f}]")
    print("\nMagnitude Statistics:")
    print(f"Raw data - Mean: {np.mean(raw_magnitudes):.4f}, Std: {np.std(raw_magnitudes):.4f}")
    print(f"Calibrated data - Mean: {np.mean(cal_magnitudes):.4f}, Std: {np.std(cal_magnitudes):.4f}")
    
    # Create calibration parameters dictionary
    calibration_params = {
        "bias": bias.tolist(),
        "transform_matrix": transform_matrix.tolist(),
        "statistics": {
            "raw_magnitude_mean": float(np.mean(raw_magnitudes)),
            "raw_magnitude_std": float(np.std(raw_magnitudes)),
            "calibrated_magnitude_mean": float(np.mean(cal_magnitudes)),
            "calibrated_magnitude_std": float(np.std(cal_magnitudes))
        },
        "ellipsoid_params": {
            "center": center.tolist(),
            "radii": radii.tolist(),
            "rotation_matrix": evecs.tolist()
        }
    }
    
    return calibration_params, calibrated_df, center, radii, evecs

def create_2d_plots(raw_data, cal_data, save_dir):
    """Create 2D plots for each pair of axes."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Define axis pairs and titles
    axis_pairs = [('ax', 'ay'), ('ax', 'az'), ('ay', 'az')]
    titles = ['X-Y Plane', 'X-Z Plane', 'Y-Z Plane']
    
    for i, (x_axis, y_axis) in enumerate(axis_pairs):
        plt.figure(figsize=(10, 10))
        
        # Plot raw and calibrated data
        plt.scatter(raw_data[x_axis], raw_data[y_axis], c='blue', alpha=0.5, label='Raw')
        plt.scatter(cal_data[x_axis], cal_data[y_axis], c='red', alpha=0.5, label='Calibrated')
        
        # Add unit circle
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = np.cos(theta)
        y_circle = np.sin(theta)
        plt.plot(x_circle, y_circle, 'g--', alpha=0.7, label='Unit Circle')
        
        plt.title(titles[i], fontsize=16)
        plt.xlabel(f"{x_axis[1].upper()}-axis", fontsize=14)
        plt.ylabel(f"{y_axis[1].upper()}-axis", fontsize=14)
        plt.grid(True)
        plt.axis('equal')
        
        # Set axis limits to show both raw and calibrated data
        max_range = max(
            abs(raw_data[x_axis].max()), abs(raw_data[x_axis].min()),
            abs(raw_data[y_axis].max()), abs(raw_data[y_axis].min()),
            1.5  # Ensure unit circle is visible
        )
        plt.xlim(-max_range, max_range)
        plt.ylim(-max_range, max_range)
        
        plt.legend(loc='upper right', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'2d_plot_{x_axis[1]}_{y_axis[1]}.png'), dpi=300)
        plt.close()

def plot_ellipsoid(ax, center, radii, rotation, color='b', alpha=0.2, label=None):
    """
    Plot an ellipsoid on the given axis.
    """
    # Generate points on a unit sphere
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    
    # Apply radii scaling
    for i in range(len(x)):
        for j in range(len(x[i])):
            x[i,j] *= radii[0]
            y[i,j] *= radii[1]
            z[i,j] *= radii[2]
            
            # Apply rotation
            p = np.dot(rotation, [x[i,j], y[i,j], z[i,j]])
            x[i,j] = p[0]
            y[i,j] = p[1]
            z[i,j] = p[2]
    
    # Apply translation
    x += center[0]
    y += center[1]
    z += center[2]
    
    # Plot ellipsoid surface
    return ax.plot_surface(x, y, z, color=color, alpha=alpha, label=label)

def create_3d_plots(raw_data, cal_data, center, radii, evecs, save_dir):
    """Create enhanced 3D plots of the accelerometer data."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Extract data
    x_raw = raw_data['ax'].values
    y_raw = raw_data['ay'].values
    z_raw = raw_data['az'].values
    
    x_cal = cal_data['ax'].values
    y_cal = cal_data['ay'].values
    z_cal = cal_data['az'].values
    
    # Calculate max range for raw data
    max_raw_range = max(
        abs(x_raw.max()), abs(x_raw.min()),
        abs(y_raw.max()), abs(y_raw.min()),
        abs(z_raw.max()), abs(z_raw.min())
    )
    
    # Plot 1: Raw data with fitted ellipsoid
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot raw data points
    ax.scatter(x_raw, y_raw, z_raw, c='blue', marker='o', alpha=0.6, label='Raw Data')
    
    # Plot fitted ellipsoid
    plot_ellipsoid(ax, center, radii, evecs, color='green', alpha=0.2)
    
    # Add coordinate axes
    ax.quiver(0, 0, 0, max_raw_range*0.2, 0, 0, color='r', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, max_raw_range*0.2, 0, color='g', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 0, max_raw_range*0.2, color='b', arrow_length_ratio=0.1)
    
    ax.set_xlabel('X-axis', fontsize=12)
    ax.set_ylabel('Y-axis', fontsize=12)
    ax.set_zlabel('Z-axis', fontsize=12)
    ax.set_title('Raw Accelerometer Data with Fitted Ellipsoid', fontsize=14)
    
    # Set equal aspect ratio
    ax.set_xlim(-max_raw_range, max_raw_range)
    ax.set_ylim(-max_raw_range, max_raw_range)
    ax.set_zlim(-max_raw_range, max_raw_range)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, '3d_raw_with_ellipsoid.png'), dpi=300)
    plt.close()
    
    # Plot 2: Calibrated data with unit sphere
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot calibrated data points
    ax.scatter(x_cal, y_cal, z_cal, c='red', marker='o', alpha=0.6, label='Calibrated Data')
    
    # Add unit sphere
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    x_sphere = np.outer(np.cos(u), np.sin(v))
    y_sphere = np.outer(np.sin(u), np.sin(v))
    z_sphere = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x_sphere, y_sphere, z_sphere, color='green', alpha=0.2)
    
    # Add coordinate axes
    ax.quiver(0, 0, 0, 1.5, 0, 0, color='r', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 1.5, 0, color='g', arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 0, 1.5, color='b', arrow_length_ratio=0.1)
    
    ax.set_xlabel('X-axis', fontsize=12)
    ax.set_ylabel('Y-axis', fontsize=12)
    ax.set_zlabel('Z-axis', fontsize=12)
    ax.set_title('Calibrated Accelerometer Data with Unit Sphere', fontsize=14)
    
    # Set equal aspect ratio
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_zlim(-1.5, 1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, '3d_calibrated_with_sphere.png'), dpi=300)
    plt.close()
    
    # Plot 3: Comparison plot (raw and calibrated) from multiple angles
    angles = [(30, 30), (30, 120), (30, 210), (30, 300)]
    
    for i, (elev, azim) in enumerate(angles):
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot raw data points
        ax.scatter(x_raw, y_raw, z_raw, c='blue', marker='o', alpha=0.4, label='Raw Data')
        
        # Plot fitted ellipsoid
        plot_ellipsoid(ax, center, radii, evecs, color='blue', alpha=0.1)
        
        # Plot calibrated data points
        ax.scatter(x_cal, y_cal, z_cal, c='red', marker='o', alpha=0.4, label='Calibrated Data')
        
        # Add unit sphere
        ax.plot_surface(x_sphere, y_sphere, z_sphere, color='green', alpha=0.1)
        
        # Set view angle
        ax.view_init(elev=elev, azim=azim)
        
        ax.set_xlabel('X-axis', fontsize=12)
        ax.set_ylabel('Y-axis', fontsize=12)
        ax.set_zlabel('Z-axis', fontsize=12)
        ax.set_title(f'Comparison View (Elevation: {elev}°, Azimuth: {azim}°)', fontsize=14)
        
        # Set equal aspect ratio to fit both datasets
        max_range = max(max_raw_range, 1.5)
        ax.set_xlim(-max_range, max_range)
        ax.set_ylim(-max_range, max_range)
        ax.set_zlim(-max_range, max_range)
        
        # Add legend
        ax.legend(loc='upper right', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'3d_comparison_angle_{i+1}.png'), dpi=300)
        plt.close()

def save_calibration_params(params, filename):
    """Save calibration parameters to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(params, f, indent=2)
        print(f"[INFO]: Calibration parameters saved to {filename}")
        return True
    except Exception as e:
        print(f"[ERROR]: Failed to save calibration parameters: {e}")
        return False

def main():
    # Create output directory
    if not os.path.exists(FIGURE_DIR):
        os.makedirs(FIGURE_DIR)
    
    # Read data
    print(f"[INFO]: Reading data from {INPUT_FILE}...")
    data = read_data(INPUT_FILE)
    if data is None:
        return
    
    print(f"[INFO]: Loaded {len(data)} data points.")
    
    # Display raw data statistics
    print("\nRaw Data Statistics:")
    print(data.describe())
    
    # Calculate raw data magnitudes
    magnitudes = np.sqrt(data['ax']**2 + data['ay']**2 + data['az']**2)
    print(f"\nRaw Magnitude Statistics:")
    print(f"  Mean: {magnitudes.mean():.4f}")
    print(f"  Std Dev: {magnitudes.std():.4f}")
    print(f"  Min: {magnitudes.min():.4f}")
    print(f"  Max: {magnitudes.max():.4f}")
    
    # Calibrate the data
    print("\n[INFO]: Performing ellipsoid fitting calibration...")
    calibration_params, calibrated_data, center, radii, evecs = calibrate_accelerometer(data)
    
    # Save calibration parameters
    save_calibration_params(calibration_params, OUTPUT_FILE)
    
    # Create plots
    print("[INFO]: Creating 2D plots...")
    create_2d_plots(data, calibrated_data, FIGURE_DIR)
    
    print("[INFO]: Creating 3D plots...")
    create_3d_plots(data, calibrated_data, center, radii, evecs, FIGURE_DIR)
    
    # Save calibrated data
    calibrated_data.to_csv(os.path.splitext(INPUT_FILE)[0] + "_calibrated.csv", index=False)
    print(f"[INFO]: Calibrated data saved to {os.path.splitext(INPUT_FILE)[0] + '_calibrated.csv'}")
    
    print("\n[INFO]: Calibration complete!")
    print(f"[INFO]: Plots saved to {FIGURE_DIR} directory")

if __name__ == "__main__":
    main()