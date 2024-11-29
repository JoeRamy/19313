#include <MQUnifiedsensor.h>
#include <DHT.h>
#include <SoftwareSerial.h>

// Pin Definitions
#define MQ7PIN A2
#define BUZZER_PIN 8
#define LED_PIN 13

// Constants
#define type 7
#define numReadings 10

// Bluetooth Serial
SoftwareSerial bluetooth(9, 11); // RX, TX

// Sensor Declarations
MQUnifiedsensor MQ7(MQ7PIN, type);
DHT dht(A0, DHT11); // Using DHT11 sensor

// Variables
float heatIndexValues[numReadings];
float airQualityIndexValues[numReadings];
int currentIndex = 0;

void setup() {
  Serial.begin(9600);
  bluetooth.begin(9600);
  dht.begin();
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  MQ7.inicializar(); // Initialize the MQ7 sensor
}

void loop() {
  // Read DHT sensor data
  float temperatureC = dht.readTemperature();
  float temperatureF = (temperatureC * 9 / 5) + 32;
  float humidity = dht.readHumidity();

  if (isnan(temperatureC) || isnan(humidity)) {
    bluetooth.println("Failed to read from the DHT sensor!");
    return;
  }

  // Update MQ7 sensor data
  MQ7.update();
  float coLevelPPM = MQ7.readSensor("CO");
  float coLevel = coLevelPPM * 1.1452;

  // Calculate heat index and air quality index
  float heatIndex = calculateHeatIndex(temperatureF, humidity);
  int airQualityIndex = calculateAQI(coLevel);

  // Store data for statistical calculations
  heatIndexValues[currentIndex] = heatIndex;
  airQualityIndexValues[currentIndex] = airQualityIndex;
  currentIndex = (currentIndex + 1) % numReadings;

  float meanHeatIndex = calculateMean(heatIndexValues, numReadings);
  float meanAQI = calculateMean(airQualityIndexValues, numReadings);
  float stdDevHeatIndex = calculateStandardDeviation(heatIndexValues, numReadings, meanHeatIndex);
  float stdDevAQI = calculateStandardDeviation(airQualityIndexValues, numReadings, meanAQI);

  // Trigger alarm if thresholds are exceeded
  if (heatIndex >= 102 || airQualityIndex >= 150) {
    triggerAlarm();
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  // Send data over Bluetooth
  sendBluetoothData(temperatureC, humidity, coLevel, heatIndex, airQualityIndex, meanHeatIndex, stdDevHeatIndex, meanAQI, stdDevAQI);

  // Print data to Serial Monitor
  printSerialData(temperatureC, humidity, coLevel, heatIndex, airQualityIndex);

  delay(5000);
}

float calculateHeatIndex(float temperatureF, float humidity) {
  return -42.379 + 2.04901523 * temperatureF + 10.14333127 * humidity - 
         0.22475541 * temperatureF * humidity - 6.83783e-3 * pow(temperatureF, 2) - 
         5.481717e-2 * pow(humidity, 2) + 1.22874e-3 * pow(temperatureF, 2) * humidity + 
         8.5282e-4 * temperatureF * pow(humidity, 2) - 1.99e-6 * pow(temperatureF, 2) * pow(humidity, 2);
}

int calculateAQI(float coLevel) {
  if (coLevel <= 5) return map(coLevel, 0, 5, 0, 50);
  if (coLevel <= 10) return map(coLevel, 5, 10, 50, 100);
  if (coLevel <= 35) return map(coLevel, 10, 35, 100, 150);
  if (coLevel <= 60) return map(coLevel, 35, 60, 150, 200);
  if (coLevel <= 90) return map(coLevel, 60, 90, 200, 300);
  if (coLevel <= 120) return map(coLevel, 90, 120, 300, 400);
  if (coLevel <= 150) return map(coLevel, 120, 150, 400, 500);
  return 500;
}

float calculateMean(float arr[], int size) {
  float sum = 0;
  for (int i = 0; i < size; i++) sum += arr[i];
  return sum / size;
}

float calculateStandardDeviation(float arr[], int size, float mean) {
  float sum = 0;
  for (int i = 0; i < size; i++) sum += pow(arr[i] - mean, 2);
  return sqrt(sum / size);
}

void triggerAlarm() {
  for (int i = 0; i <= 10; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(LED_PIN, HIGH);
    delay(10);
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
  }
}

void sendBluetoothData(float temperatureC, float humidity, float coLevel, float heatIndex, int airQualityIndex, 
                       float meanHeatIndex, float stdDevHeatIndex, float meanAQI, float stdDevAQI) {
  bluetooth.print(temperatureC); bluetooth.print(",");
  bluetooth.print(humidity); bluetooth.print(",");
  bluetooth.print(coLevel); bluetooth.print(",");
  bluetooth.print(heatIndex); bluetooth.print(",");
  bluetooth.print(airQualityIndex); bluetooth.print(",");
  bluetooth.print(meanHeatIndex); bluetooth.print(",");
  bluetooth.print(stdDevHeatIndex); bluetooth.print(",");
  bluetooth.print(meanAQI); bluetooth.print(",");
  bluetooth.println(stdDevAQI);
}

void printSerialData(float temperatureC, float humidity, float coLevel, float heatIndex, int airQualityIndex) {
  Serial.print("Temperature: "); Serial.print(temperatureC); Serial.print(" C | ");
  Serial.print("Humidity: "); Serial.print(humidity); Serial.print(" % | ");
  Serial.print("CO: "); Serial.print(coLevel, 2); Serial.print(" ppm | ");
  Serial.print("Heat Index: "); Serial.print(heatIndex); Serial.print(" | ");
  Serial.print("AQI: "); Serial.println(airQualityIndex);
}
