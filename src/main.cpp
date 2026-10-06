#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);

  // ESP32:
  // SDA = GPIO 21
  // SCL = GPIO 22
  Wire.begin(21, 22);

  Serial.println("Dang khoi dong MPU6050...");

  if (!mpu.begin()) {
    Serial.println("Khong tim thay MPU6050!");
    while (1) {
      delay(1000);
    }
  }

  // The impact threshold is >2 g; the library's default +/-2 g range
  // clips a single-axis impact before Python can recognize it.
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

  Serial.println("MPU6050 da san sang!");
}

void loop() {
  sensors_event_t accel;
  sensors_event_t gyro;
  sensors_event_t temp;

  mpu.getEvent(&accel, &gyro, &temp);

  // Chuyển acceleration từ m/s² sang g
  float ax = accel.acceleration.x / 9.80665;
  float ay = accel.acceleration.y / 9.80665;
  float az = accel.acceleration.z / 9.80665;

  // Chuyển gyro từ rad/s sang độ/s
  float gx = gyro.gyro.x * 180.0 / PI;
  float gy = gyro.gyro.y * 180.0 / PI;
  float gz = gyro.gyro.z * 180.0 / PI;

  // Chỉ in một dòng để Python dễ đọc
  Serial.print("SENSOR,");
  Serial.print(ax, 3);
  Serial.print(",");
  Serial.print(ay, 3);
  Serial.print(",");
  Serial.print(az, 3);
  Serial.print(",");
  Serial.print(gx, 3);
  Serial.print(",");
  Serial.print(gy, 3);
  Serial.print(",");
  Serial.println(gz, 3);

  delay(20);  // ~50 Hz: capture brief motion before the slower vision loop.
}
