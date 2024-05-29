import psutil
import matplotlib.pyplot as plt
from tabulate import tabulate
import threading
import time

class HardwareScanner:
    def __init__(self):
        self.cpu_info = None
        self.mem_info = None
        self.disk_info = None

    def scan_cpu_info(self):
        self.cpu_info = {
            "Physical Cores": psutil.cpu_count(logical=False),
            "Logical Cores": psutil.cpu_count(logical=True),
            "CPU Frequency (MHz)": psutil.cpu_freq().current,
            "CPU Usage (%)": psutil.cpu_percent(interval=1, percpu=True)
        }

    def scan_mem_info(self):
        virtual_mem = psutil.virtual_memory()
        self.mem_info = {
            "Total Memory (MB)": virtual_mem.total // (1024 * 1024),
            "Available Memory (MB)": virtual_mem.available // (1024 * 1024),
            "Used Memory (MB)": virtual_mem.used // (1024 * 1024),
            "Memory Usage (%)": virtual_mem.percent
        }

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

def monitor_realtime(scanner):
    plt.ion()
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.5)

    while True:
        cpu_info, mem_info, _ = scanner.get_hardware_info()

        # Plot CPU Usage
        axes[0].clear()
        axes[0].bar(range(len(cpu_info["CPU Usage (%)"])), cpu_info["CPU Usage (%)"])
        axes[0].set_title('CPU Usage (%)')
        axes[0].set_xlabel('CPU Core')
        axes[0].set_ylabel('Usage (%)')
        axes[0].set_xticks(range(len(cpu_info["CPU Usage (%)"])))

        # Plot Memory Usage
        axes[1].clear()
        axes[1].bar(['Used', 'Available'], [mem_info["Used Memory (MB)"], mem_info["Available Memory (MB)"]], color=['blue', 'green'])
        axes[1].set_title('Memory Usage')
        axes[1].set_ylabel('Memory (MB)')

        plt.pause(1)

def display_hardware_info(cpu_info, mem_info, disk_info):
    print("CPU Information:")
    print(tabulate(cpu_info.items(), headers=['Attribute', 'Value']))
    print("\nMemory Information:")
    print(tabulate(mem_info.items(), headers=['Attribute', 'Value']))
    print("\nDisk Information:")
    print(tabulate([list(disk.values()) for disk in disk_info], headers=disk_info[0].keys()))

def main():
    scanner = HardwareScanner()
    scanner.scan_hardware()
    cpu_info, mem_info, disk_info = scanner.get_hardware_info()

    display_hardware_info(cpu_info, mem_info, disk_info)

    print("\nMonitoring CPU and Memory usage in real-time. Close the plot window to stop.")
    monitor_realtime(scanner)

if __name__ == "__main__":
    main()
