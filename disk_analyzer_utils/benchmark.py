#======================================================
# Import
import os
import csv
from datetime import datetime
import psutil

#======================================================
# Logs performance metrics into a CSV file
def log_benchmark(
    path, item_count, total_size, elapsed_time, version, max_threads=None, filename="benchmark_log.csv"
):
    header = [
        "version", "timestamp", "path", "item_count", "total_size_bytes",
        "elapsed_time_sec", "cpu_percent", "mem_percent",
        "proc_read_bytes", "proc_write_bytes",
        "num_threads", "max_threads"
    ]

    pid = os.getpid()
    proc = psutil.Process(pid)
    cpu_pct = proc.cpu_percent(interval=0.5)
    mem_bytes = proc.memory_info().rss
    mem_pct = mem_bytes / psutil.virtual_memory().total * 100
    io = proc.io_counters()
    proc_read_bytes = io.read_bytes
    proc_write_bytes = io.write_bytes
    num_threads = proc.num_threads()

    row = [
        version,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        path,
        item_count,
        total_size,
        f"{elapsed_time:.4f}",
        f"{cpu_pct:.1f}",
        f"{mem_pct:.1f}",
        proc_read_bytes,
        proc_write_bytes,
        num_threads,
        max_threads
    ]

    write_header = not os.path.exists(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)
