#include "Wire.h"

// Constants
const int MPU_ADDR = 0x68;      // MPU6050 I2C address (0x69 if AD0 pin is HIGH)
const float ACC_SCALE = 16384.0; // Scale factor for +/-2g range
const bool PRINT_TIMESTAMP = true; // Whether to include timestamps in output
const int SAMPLE_RATE_MS = 100;   // Sample every 10ms (100Hz)

// Variables for sensor data
int16_t acc_x, acc_y, acc_z;
int16_t gyro_x, gyro_y, gyro_z;
int16_t temperature;

void setup() {
  // Initialize serial communication
  Serial.begin(9600); // Higher baud rate for faster data transfer
  
  // Initialize MPU6050
  Wire.begin();
  initMPU6050();
  
  // Print CSV header
  if (PRINT_TIMESTAMP) {
    Serial.println("timestamp_ms,acc_x,acc_y,acc_z");
  } else {
    Serial.println("acc_x,acc_y,acc_z");
  }
}

void loop() {
  // Read sensor data
  readMPU6050Data();
  
  // Print data in CSV format
  if (PRINT_TIMESTAMP) {
    Serial.print(millis());
    Serial.print(",");
  }
  
  // Convert raw values to g units and print with 6 decimal precision
  Serial.print(acc_x / ACC_SCALE, 6);
  Serial.print(",");
  Serial.print(acc_y / ACC_SCALE, 6);
  Serial.print(",");
  Serial.println(acc_z / ACC_SCALE, 6);
  
  // Maintain consistent sampling rate
  delay(SAMPLE_RATE_MS);
}

void initMPU6050() {
  // Wake up the MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);  // PWR_MGMT_1 register
  Wire.write(0);     // Set to zero (wakes up the MPU-6050)
  Wire.endTransmission(true);
  
  // Configure accelerometer range to ±2g
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);  // ACCEL_CONFIG register
  Wire.write(0x00);  // 0x00 = ±2g, 0x08 = ±4g, 0x10 = ±8g, 0x18 = ±16g
  Wire.endTransmission(true);
}

void readMPU6050Data() {
  // Request data from MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);  // Starting register address (ACCEL_XOUT_H)
  Wire.endTransmission(false);  // Keep connection active
  Wire.requestFrom(MPU_ADDR, 14, true);  // Request 14 bytes
  
  // Read accelerometer data
  acc_x = Wire.read() << 8 | Wire.read();  // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  acc_y = Wire.read() << 8 | Wire.read();  // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  acc_z = Wire.read() << 8 | Wire.read();  // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
  
  // Read temperature data (not used but need to read to get to gyro data)
  temperature = Wire.read() << 8 | Wire.read();
  
  // Read gyroscope data (not used in this version but available)
  gyro_x = Wire.read() << 8 | Wire.read();
  gyro_y = Wire.read() << 8 | Wire.read();
  gyro_z = Wire.read() << 8 | Wire.read();
}