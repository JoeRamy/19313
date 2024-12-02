import serial
import sqlite3
import time
from datetime import datetime
import threading

# Serial Port Settings
serial_port = 'COM12'  # Update this based on your HC06 Bluetooth COM port
baud_rate = 9600

# SQLite Database Path
db_path = 'D:\\Joee\\T3\\SensorsReadings.db'

# Open Serial Connection
try:
    ser = serial.Serial(serial_port, baud_rate)
    time.sleep(2)  # Wait for connection to establish
    print("Bluetooth connected successfully.")
except serial.SerialException as e:
    print(f"Error connecting to Bluetooth: {e}")
    exit()

# Data batch handling
readings_batch = []
batch_size = 1  # Adjust batch size for testing or real-time operation

def create_table(cursor):
    """Create the sensor readings table if it doesn't exist."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            real_time TEXT,
            temperature REAL,
            humidity REAL,
            co_level REAL,
            heat_index REAL,
            air_quality_index REAL,
            mean_heat_index REAL,
            std_dev_heat_index REAL,
            mean_aqi REAL,
            std_dev_aqi REAL
        )
    ''')
    print("Table created or verified successfully.")

def process_data(line, cursor, conn):
    """Process the incoming data and add it to the SQLite database in batches."""
    global readings_batch
    data = line.split(',')

    # Print the raw data received for debugging
    print(f"Raw data received: {repr(line)}")

    if len(data) == 9:  # Expecting 9 values based on the updated Arduino code
        try:
            # Extract real-time sensor readings
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            temperature = float(data[0])
            humidity = float(data[1])
            co_level = float(data[2])
            heat_index = float(data[3])
            air_quality_index = float(data[4])
            mean_heat_index = float(data[5])
            std_dev_heat_index = float(data[6])
            mean_aqi = float(data[7])
            std_dev_aqi = float(data[8])

            # Add the reading to the batch
            readings_batch.append((timestamp, temperature, humidity, co_level, heat_index, air_quality_index,
                                   mean_heat_index, std_dev_heat_index, mean_aqi, std_dev_aqi))

            # If the batch reaches the required size, insert into the database
            if len(readings_batch) >= batch_size:
                try:
                    cursor.executemany('''
                        INSERT INTO sensor_readings (
                            real_time, temperature, humidity, co_level, heat_index, 
                            air_quality_index, mean_heat_index, std_dev_heat_index, 
                            mean_aqi, std_dev_aqi
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', readings_batch)
                    conn.commit()
                    print("Data committed to the database.")
                    
                    # Confirm insertion by querying the last entry
                    cursor.execute("SELECT * FROM sensor_readings ORDER BY rowid DESC LIMIT 1")
                    last_entry = cursor.fetchone()
                    print("Last entry in the database:", last_entry)

                    readings_batch.clear()  # Clear the batch after committing
                except sqlite3.Error as e:
                    print(f"Error inserting data into database: {e}")

        except ValueError as e:
            print(f"Error in processing data: {e}")

def read_bluetooth():
    """Read data from the Bluetooth module continuously."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the table if not exists
    create_table(cursor)

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()  # Read the line from Bluetooth
                process_data(line, cursor, conn)
    except Exception as e:
        print(f"Error reading Bluetooth: {e}")
    finally:
        conn.close()
        print("Database connection closed.")

# Run the Bluetooth reading in a separate thread
bluetooth_thread = threading.Thread(target=read_bluetooth)
bluetooth_thread.start()

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    ser.close()
    print("Serial connection closed.")
