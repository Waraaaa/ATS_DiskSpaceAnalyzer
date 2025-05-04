#======================================================
# Import
import os
import sys
import shutil
import time
import psutil
from disk_analyzer_utils.plotting import plot
from disk_analyzer_utils.benchmark import log_benchmark
from disk_analyzer_utils.utils import show_analysis

#======================================================
# Get total size of all files in a folder (and subfolders)
def get_size(start_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path, onerror=lambda e: None):  # Traverse directories
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):  # Skip symbolic links
                    total_size += os.path.getsize(fp)  # Add file size
            except Exception:
                pass  # Ignore errors (e.g., permission issues)
    return total_size

#======================================================
# Analyze disk usage for items in the given folder
def analyze(base_path="/"):
    print(f"Analyzing: {base_path}")
    start_time = time.time()

    total, used, free = shutil.disk_usage(base_path)  # Get disk usage stats
    scanned = set()  # Track visited paths
    disk_data = []  # Store results
    item_count = 0
    total_size_collected = 0

    #======================================================
    # Loop through items in the folder
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        try:
            real_path = os.path.realpath(item_path)
            if real_path in scanned:
                continue  # Skip if already scanned
            scanned.add(real_path)

            #======================================================
            # Get size of folder or file
            if os.path.isdir(item_path):
                size = get_size(item_path)
            elif os.path.isfile(item_path):
                size = os.path.getsize(item_path)
            else:
                continue  # Skip if not a file/folder

            #======================================================
            # Skip temp files
            SKIP_EXTENSIONS = [".tmp"]
            _, ext = os.path.splitext(item)
            if ext.lower() in SKIP_EXTENSIONS:
                continue

            disk_data.append({"path": item, "size": size})
            item_count += 1
            total_size_collected += size

        except Exception as e:
            print(f"{item_path:<30} ERROR: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Analyze time: {elapsed_time} s.")
    process = psutil.Process(os.getpid())
    print(f"Memory used: {process.memory_info().rss / 1024 ** 2:.2f} MB")

    #======================================================
    # Display results in chart and text
    show_analysis(disk_data, total, used, free)
    plot(disk_data, base_path)
    log_benchmark(base_path, item_count, total_size_collected, elapsed_time, version="base")

#======================================================
# Main loop to analyze folders and navigate subdirectories
def analyzer(start_drive):
    nested_directory = 0
    analyze(start_drive)  # Analyze root folder
    nested_directory += 1

    old_path = [start_drive]
    path = start_drive

    while True:
        print("-" * 55)
        try:
            entries = os.listdir(path)
            dirs = [d for d in entries if os.path.isdir(os.path.join(path, d))]  # Show only folders
        except Exception as e:
            print(f"Error accessing directory: {e}")
            if len(old_path) > 1:
                path = old_path.pop()  # Go back if error occurs
                nested_directory -= 1
                continue
            else:
                sys.exit(1)

        #======================================================
        # Show menu for folder navigation
        if not dirs:
            print('No more subdirectories here. ("exit" to end, "0" to go back)')
        else:
            for idx, d in enumerate(dirs, start=1):
                print(f"{idx}: {d}")
            print('Select a directory number to analyze ("exit" to end, "0" to go back):')

        choice = input("> ").strip()
        if choice.lower() == "exit":
            sys.exit(0)

        if choice == "0":
            if nested_directory == 1:
                return True  # Restart from root folder
            elif old_path:
                path = old_path.pop()  # Go up one level
                nested_directory -= 1
                continue
            else:
                continue

        try:
            num = int(choice)
        except ValueError:
            print(f'"{choice}" is not a valid number. Try again.')
            continue

        if num < 1 or num > len(dirs):
            print(f'"{num}" is out of range. Try again.')
            continue

        #======================================================
        # Navigate into selected folder
        old_path.append(path)
        path = os.path.join(path, dirs[num - 1])
        analyze(path)
        nested_directory += 1
