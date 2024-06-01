import psutil
import matplotlib.pyplot as plt
import threading
import time
import sqlite3
from flask import Flask, render_template, jsonify

# Database handler class to manage database operations
class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect('hardware_monitoring.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cpu_usage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            core_id INTEGER,
                            usage FLOAT
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS memory_usage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            used_memory INTEGER,
                            available_memory INTEGER
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS disk_usage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            mountpoint TEXT,
                            usage FLOAT
                        )''')
        self.conn.commit()

    def insert_cpu_usage(self, core_id, usage):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO cpu_usage (core_id, usage) VALUES (?, ?)''', (core_id, usage))
        self.conn.commit()

    def insert_memory_usage(self, used_memory, available_memory):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO memory_usage (used_memory, available_memory) VALUES (?, ?)''', (used_memory, available_memory))
        self.conn.commit()

    def insert_disk_usage(self, mountpoint, usage):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO disk_usage (mountpoint, usage) VALUES (?, ?)''', (mountpoint, usage))
        self.conn.commit()

    def fetch_cpu_usage(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM cpu_usage ORDER BY timestamp DESC LIMIT 100''')
        return cursor.fetchall()

    def fetch_memory_usage(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM memory_usage ORDER BY timestamp DESC LIMIT 100''')
        return cursor.fetchall()

    def fetch_disk_usage(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM disk_usage ORDER BY timestamp DESC LIMIT 100''')
        return cursor.fetchall()

# Initialize Flask application
app = Flask(__name__)
db_handler = DatabaseHandler()

# Define routes for web interface
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cpu_usage')
def api_cpu_usage():
    cpu_usage_data = db_handler.fetch_cpu_usage()
    return jsonify(cpu_usage_data)

@app.route('/api/memory_usage')
def api_memory_usage():
    memory_usage_data = db_handler.fetch_memory_usage()
    return jsonify(memory_usage_data)

@app.route('/api/disk_usage')
def api_disk_usage():
    disk_usage_data = db_handler.fetch_disk_usage()
    return jsonify(disk_usage_data)

# Hardware scanner class to collect hardware usage data
class HardwareScanner:
    def __init__(self, db_handler):
        self.cpu_info = None
        self.mem_info = None
        self.disk_info = None
        self.db_handler = db_handler

    def scan_cpu_info(self):
        self.cpu_info = {
            "Physical Cores": psutil.cpu_count(logical=False),
            "Logical Cores": psutil.cpu_count(logical=True),
            "CPU Frequency (MHz)": psutil.cpu_freq().current,
            "CPU Usage (%)": psutil.cpu_percent(interval=1, percpu=True)
        }
        for core_id, usage in enumerate(self.cpu_info["CPU Usage (%)"]):
            self.db_handler.insert_cpu_usage(core_id, usage)

    def scan_mem_info(self):
        virtual_mem = psutil.virtual_memory()
        self.mem_info = {
            "Total Memory (MB)": virtual_mem.total // (1024 * 1024),
            "Available Memory (MB)": virtual_mem.available // (1024 * 1024),
            "Used Memory (MB)": virtual_mem.used // (1024 * 1024),
            "Memory Usage (%)": virtual_mem.percent
        }
        self.db_handler.insert_memory_usage(self.mem_info["Used Memory (MB)"], self.mem_info["Available Memory (MB)"])

    def scan_disk_info(self):
        self.disk_info = []
        for partition in psutil.disk_partitions():
            disk_usage = psutil.disk_usage(partition.mountpoint)
            self.disk_info.append({
                "Mountpoint": partition.mountpoint,
                "File System Type": partition.fstype,
                "Total Size (GB)": disk_usage.total // (2**30),
                "Used Size (GB)": disk_usage.used // (2**30),
                "Free Size (GB)": disk_usage.free // (2**30),
                "Disk Usage (%)": disk_usage.percent
            })
            self.db_handler.insert_disk_usage(partition.mountpoint, disk_usage.percent)

    def scan_hardware(self):
        threads = []
        for scan_func in [self.scan_cpu_info, self.scan_mem_info, self.scan_disk_info]:
            thread = threading.Thread(target=scan_func)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def get_hardware_info(self):
        return self.cpu_info, self.mem_info, self.disk_info

# Hardware monitor class to manage real-time monitoring and analysis
class HardwareMonitor:
    def __init__(self, scanner, db_handler):
        self.scanner = scanner
        self.db_handler = db_handler

    def monitor_realtime(self):
        while True:
            self.scanner.scan_hardware()
            time.sleep(1)

# Main function to initialize and run hardware monitoring components
def main():
    scanner = HardwareScanner(db_handler)
    monitor = HardwareMonitor(scanner, db_handler)

    # Start the hardware monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor.monitor_realtime)
    monitor_thread.start()

    # Start Flask app for web interface
    app.run(debug=True, threaded=True)

if __name__ == "__main__":
    main()
