import serial
import sqlite3
import time
from datetime import datetime
import threading
import serial.tools.list_ports
import os

# SQLite Database Path
db_path = os.path.expanduser('~/SensorsReadings.db')  # Default to user's home directory

# Baud Rate for HC-06 Bluetooth
baud_rate = 9600

# Serial connection variables
ser = None
readings_batch = []
batch_size = 1  # Adjust batch size for real-time or testing
last_data_time = time.time()


def ensure_db_directory_exists():
    """Ensure the directory for the database file exists."""
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created directory for database: {db_dir}")


def list_serial_ports():
    """List all available serial ports on the system."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def open_serial_connection(max_attempts=5):
    """
    Scan and connect to an available Bluetooth serial port.
    Retry multiple attempts for each port.
    """
    global ser
    ports = list_serial_ports()
    if not ports:
        print("No serial ports detected. Please check the Bluetooth device connection.")
        return None

    for port in ports:
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Attempting to connect to {port} (Attempt {attempt}/{max_attempts})...")
                ser = serial.Serial(port, baud_rate, timeout=1)
                time.sleep(2)  # Allow time for connection
                print(f"Bluetooth connected successfully on {port}.")
                return ser
            except serial.SerialException as e:
                print(f"Failed to connect to {port}: {e}")
            time.sleep(1)  # Wait before retrying
    print("Failed to establish a Bluetooth connection on any port.")
    return None


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
    global readings_batch, last_data_time
    data = line.split(',')

    print(f"Raw data received: {repr(line)}")  # Print raw data for debugging

    if len(data) == 9:  # Expecting 9 values
        try:
            # Extract sensor readings
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

            # Add reading to batch
            readings_batch.append((timestamp, temperature, humidity, co_level, heat_index, air_quality_index,
                                   mean_heat_index, std_dev_heat_index, mean_aqi, std_dev_aqi))

            # Update the last data time
            last_data_time = time.time()

            # Insert data into the database once batch is ready
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

                    # Print the last inserted entry for confirmation
                    cursor.execute("SELECT * FROM sensor_readings ORDER BY rowid DESC LIMIT 1")
                    last_entry = cursor.fetchone()
                    print("Last entry in the database:", last_entry)

                    readings_batch.clear()  # Clear batch after committing
                except sqlite3.Error as e:
                    print(f"Database insertion error: {e}")
        except ValueError as e:
            print(f"Data processing error: {e}")


def reconnect_bluetooth():
    """Attempt to reconnect to Bluetooth if the connection is lost."""
    global ser
    ser = None
    while ser is None:
        print("Reconnecting to Bluetooth...")
        ser = open_serial_connection()
        if ser:
            print("Reconnected successfully.")
        else:
            print("Reconnection failed. Retrying in 2 seconds...")
            time.sleep(2)


def read_bluetooth():
    """Read data from the Bluetooth module continuously."""
    global ser, last_data_time
    ensure_db_directory_exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    create_table(cursor)

    try:
        while True:
            # Check for timeout (no data received for more than 10 seconds)
            if time.time() - last_data_time > 10:
                print("No data received for 10 seconds. Restarting connection...")
                reconnect_bluetooth()

            if ser is None or not ser.is_open:
                reconnect_bluetooth()

            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    process_data(line, cursor, conn)
            except (serial.SerialException, OSError) as e:
                print(f"Bluetooth connection lost: {e}. Reconnecting...")
                ser.close()  # Close the current connection before trying to reconnect
                reconnect_bluetooth()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        conn.close()
        if ser and ser.is_open:
            ser.close()
        print("Database and serial connections closed.")


# Run the Bluetooth reading in a separate thread
bluetooth_thread = threading.Thread(target=read_bluetooth, daemon=True)
bluetooth_thread.start()

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    if ser and ser.is_open:
        ser.close()
    print("Serial connection closed.")
