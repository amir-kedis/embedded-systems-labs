import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os

def plot_imu_data(csv_file_path):
    """
    Plot IMU data from a CSV file showing accelerometer and gyroscope readings over time.
    
    Args:
        csv_file_path (str): Path to the CSV file containing IMU data
    """
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found.")
        return
    
    # Read the data from CSV file
    try:
        print(f"Reading data from {csv_file_path}...")
        df = pd.read_csv(csv_file_path)
        print(f"Successfully loaded data with {len(df)} samples.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Check required columns
    required_columns = ['seconds_elapsed', 'x_acc', 'y_acc', 'z_acc', 'x_gyro', 'y_gyro', 'z_gyro']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Error: Missing required columns: {', '.join(missing_columns)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return
    
    # Print data summary
    print("\nData Summary:")
    print(f"Time range: {df['seconds_elapsed'].min():.2f}s to {df['seconds_elapsed'].max():.2f}s")
    print(f"Accelerometer X range: {df['x_acc'].min():.2f} to {df['x_acc'].max():.2f} g")
    print(f"Accelerometer Y range: {df['y_acc'].min():.2f} to {df['y_acc'].max():.2f} g")
    print(f"Accelerometer Z range: {df['z_acc'].min():.2f} to {df['z_acc'].max():.2f} g")
    # print(f"Gyroscope X range: {df['x_gyro'].min():.2f} to {df['x_gyro'].max():.2f} rad/s")
    # print(f"Gyroscope Y range: {df['y_gyro'].min():.2f} to {df['y_gyro'].max():.2f} rad/s")
    # print(f"Gyroscope Z range: {df['z_gyro'].min():.2f} to {df['z_gyro'].max():.2f} rad/s")
    
    # Calculate magnitudes
    df['acc_magnitude'] = np.sqrt(df['x_acc']**2 + df['y_acc']**2 + df['z_acc']**2)
    # df['gyro_magnitude'] = np.sqrt(df['x_gyro']**2 + df['y_gyro']**2 + df['z_gyro']**2)
    
    # Detect motion regions
    acc_std = np.std(df['acc_magnitude'])
    # gyro_std = np.std(df['gyro_magnitude'])
    
    motion_threshold_acc = 0.1  # Adjust based on your data
    motion_threshold_gyro = 0.1  # Adjust based on your data
    
    # motion_regions = (abs(df['acc_magnitude'] - df['acc_magnitude'].mean()) > motion_threshold_acc) | \
    #                  (abs(df['gyro_magnitude'] - df['gyro_magnitude'].mean()) > motion_threshold_gyro)
    
    # Create time series plots
    print("Creating time series plots...")
    plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
    
    # Plot accelerometer data
    ax1 = plt.subplot(gs[0])
    ax1.plot(df['seconds_elapsed'], df['x_acc'], 'r-', label='X Acceleration')
    ax1.plot(df['seconds_elapsed'], df['y_acc'], 'g-', label='Y Acceleration')
    ax1.plot(df['seconds_elapsed'], df['z_acc'], 'b-', label='Z Acceleration')
    ax1.plot(df['seconds_elapsed'], df['acc_magnitude'], 'k--', label='Magnitude', alpha=0.5)
    
    ax1.set_title('Accelerometer Readings Over Time', fontsize=14)
    ax1.set_ylabel('Acceleration (g)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper right')
    
    # Highlight motion regions
    # for i in range(1, len(motion_regions)):
    #     if motion_regions.iloc[i] and not motion_regions.iloc[i-1]:  # Start of motion
    #         ax1.axvline(x=df['seconds_elapsed'].iloc[i], color='orange', alpha=0.3)
    #     elif not motion_regions.iloc[i] and motion_regions.iloc[i-1]:  # End of motion
    #         ax1.axvline(x=df['seconds_elapsed'].iloc[i], color='green', alpha=0.3)
    
    # Plot gyroscope data
    # ax2 = plt.subplot(gs[1], sharex=ax1)
    # ax2.plot(df['seconds_elapsed'], df['x_gyro'], 'r-', label='X Gyro')
    # ax2.plot(df['seconds_elapsed'], df['y_gyro'], 'g-', label='Y Gyro')
    # ax2.plot(df['seconds_elapsed'], df['z_gyro'], 'b-', label='Z Gyro')
    # ax2.plot(df['seconds_elapsed'], df['gyro_magnitude'], 'k--', label='Magnitude', alpha=0.5)
    
    # ax2.set_title('Gyroscope Readings Over Time', fontsize=14)
    # ax2.set_xlabel('Time (seconds)', fontsize=12)
    # ax2.set_ylabel('Angular Velocity (rad/s)', fontsize=12)
    # ax2.grid(True, linestyle='--', alpha=0.7)
    # ax2.legend(loc='upper right')
    
    # Highlight the same motion regions in gyro plot
    # for i in range(1, len(motion_regions)):
    #     if motion_regions.iloc[i] and not motion_regions.iloc[i-1]:
    #         ax2.axvline(x=df['seconds_elapsed'].iloc[i], color='orange', alpha=0.3)
    #     elif not motion_regions.iloc[i] and motion_regions.iloc[i-1]:
    #         ax2.axvline(x=df['seconds_elapsed'].iloc[i], color='green', alpha=0.3)
    
    plt.tight_layout()
    
    # Create 3D visualization of accelerometer data
    print("Creating 3D visualization...")
    fig_3d = plt.figure(figsize=(10, 8))
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    
    # Create a scatter plot with time as color
    scatter = ax_3d.scatter(df['x_acc'], df['y_acc'], df['z_acc'], 
                          c=df['seconds_elapsed'], cmap='viridis',
                          s=10, alpha=0.7)
    
    # Add a colorbar to show the time mapping
    cbar = plt.colorbar(scatter)
    cbar.set_label('Time (seconds)')
    
    # Connect points with lines to show the path
    ax_3d.plot(df['x_acc'], df['y_acc'], df['z_acc'], 'gray', alpha=0.3)
    
    # Set labels and title
    ax_3d.set_xlabel('X Acceleration (g)')
    ax_3d.set_ylabel('Y Acceleration (g)')
    ax_3d.set_zlabel('Z Acceleration (g)')
    ax_3d.set_title('3D Accelerometer Data Path')
    
    # Equal aspect ratio for all axes
    max_range = max([
        df['x_acc'].max() - df['x_acc'].min(),
        df['y_acc'].max() - df['y_acc'].min(),
        df['z_acc'].max() - df['z_acc'].min()
    ])
    mid_x = (df['x_acc'].max() + df['x_acc'].min()) / 2
    mid_y = (df['y_acc'].max() + df['y_acc'].min()) / 2
    mid_z = (df['z_acc'].max() + df['z_acc'].min()) / 2
    ax_3d.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
    ax_3d.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
    ax_3d.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
    
    # Create magnitude plots
    print("Creating magnitude analysis plots...")
    plt.figure(figsize=(14, 8))
    
    # Plot total acceleration and angular velocity magnitudes
    plt.subplot(2, 1, 1)
    plt.plot(df['seconds_elapsed'], df['acc_magnitude'], 'b-', label='Acceleration Magnitude')
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='1g Reference')
    plt.title('Acceleration Magnitude Over Time')
    plt.ylabel('Acceleration (g)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # plt.subplot(2, 1, 2)
    # plt.plot(df['seconds_elapsed'], df['gyro_magnitude'], 'r-', label='Angular Velocity Magnitude')
    # plt.title('Angular Velocity Magnitude Over Time')
    # plt.xlabel('Time (seconds)')
    # plt.ylabel('Angular Velocity (rad/s)')
    # plt.grid(True, linestyle='--', alpha=0.7)
    # plt.legend()
    
    plt.tight_layout()
    
    # Save figures
    output_dir = "imu_plots"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_filename = os.path.splitext(os.path.basename(csv_file_path))[0]
    
    time_series_path = os.path.join(output_dir, f"{base_filename}_time_series.png")
    plt.figure(1).savefig(time_series_path, dpi=300, bbox_inches='tight')
    
    path_3d_path = os.path.join(output_dir, f"{base_filename}_3d_path.png")
    fig_3d.savefig(path_3d_path, dpi=300, bbox_inches='tight')
    
    magnitude_path = os.path.join(output_dir, f"{base_filename}_magnitude.png")
    plt.figure(3).savefig(magnitude_path, dpi=300, bbox_inches='tight')
    
    print(f"\nPlots saved to {output_dir} directory:")
    print(f"- Time series: {time_series_path}")
    print(f"- 3D path: {path_3d_path}")
    print(f"- Magnitude analysis: {magnitude_path}")
    
    # Show all plots
    plt.show()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Plot IMU data from CSV file")
    parser.add_argument("csv_file", help="Path to the CSV file containing IMU data")
    
    args = parser.parse_args()
    plot_imu_data(args.csv_file)