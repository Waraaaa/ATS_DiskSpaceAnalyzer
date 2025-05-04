#======================================================
# Imports
import os
import sys
import shutil
import time
import asyncio
import psutil
from disk_analyzer_utils.plotting import plot
from disk_analyzer_utils.benchmark import log_benchmark
from disk_analyzer_utils.utils import show_analysis

#======================================================
# Asynchronously calculate the total size of a folder
async def get_size(path):
    def compute_size():
        total = 0
        for dirpath, _, filenames in os.walk(path, onerror=lambda e: None):
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):  # Skip symbolic links
                        total += os.path.getsize(fp)
                except Exception:
                    pass  # Ignore unreadable files
        return total
    return await asyncio.to_thread(compute_size)

#======================================================
# Asynchronously analyze the size of a single file or folder
async def scan_item(path):
    try:
        SKIP_EXTENSIONS = [".tmp"]
        _, ext = os.path.splitext(path)
        if ext.lower() in SKIP_EXTENSIONS:
            return None  # Skip unwanted file types

        if os.path.isdir(path):  # Folder: calculate size
            size = await get_size(path)
        elif os.path.isfile(path):  # File: get size directly
            size = await asyncio.to_thread(os.path.getsize, path)
        else:
            return None  # Skip non-file/folder items

        return {"path": os.path.basename(path), "size": size}
    except Exception as e:
        print(f"{path:<30} ERROR: {e}")
        return None  # Return None for failed items

#======================================================
# Asynchronously analyze contents of a directory
async def analyze(base_path="/", max_threads=None):
    print(f"Analyzing: {base_path}")
    start_time = time.time()

    total, used, free = shutil.disk_usage(base_path)  # Get disk usage stats

    try:
        items = await asyncio.to_thread(os.listdir, base_path)  # List items in folder
    except Exception as e:
        print(f"Error listing {base_path}: {e}")
        return

    # Track scanned items (avoiding symbolic links)
    scanned, full_paths = set(), []
    for item in items:
        item_path = os.path.join(base_path, item)
        real_path = os.path.realpath(item_path)
        if real_path not in scanned:
            scanned.add(real_path)
            full_paths.append(item_path)

    # Create tasks to scan items concurrently
    tasks = [scan_item(path) for path in full_paths]
    results = await asyncio.gather(*tasks)

    # Filter out failed/skipped items
    disk_data = [r for r in results if r]
    item_count = len(disk_data)
    total_size = sum(d["size"] for d in disk_data)

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Display analysis time and memory usage
    print(f"Analyze time: {elapsed_time} s.")
    process = psutil.Process(os.getpid())
    print(f"Memory used: {process.memory_info().rss / 1024 ** 2:.2f} MB")

    # Show disk data analysis and plot
    show_analysis(disk_data, total, used, free)
    plot(disk_data, base_path)
    log_benchmark(base_path, item_count, total_size, elapsed_time, version="optimized", max_threads=max_threads)

#======================================================
# Asynchronous folder navigation loop with interactive selection
async def analyzer(start_drive, max_threads=None):
    nested_directory = 0
    await analyze(start_drive, max_threads)  # Analyze starting folder
    nested_directory += 1

    old_path = [start_drive]  # Stack to keep track of visited folders
    path = start_drive

    while True:
        print("-" * 55)
        try:
            entries = os.listdir(path)  # List directories only
            dirs = [d for d in entries if os.path.isdir(os.path.join(path, d))]
        except Exception as e:
            print(f"Error accessing directory: {e}")
            if len(old_path) > 1:  # Go back if directory can't be accessed
                path = old_path.pop()
                nested_directory -= 1
                continue
            else:
                sys.exit(1)

        if not dirs:
            print('No more subdirectories here. ("exit" to end, "0" to go back)')
        else:
            for idx, d in enumerate(dirs, start=1):
                print(f"{idx}: {d}")
            print('Select a directory number ("exit" to end, "0" to go back):')

        choice = input("> ").strip()
        if choice.lower() == "exit":
            sys.exit(0)

        if choice == "0":  # Go back to parent folder
            if nested_directory == 1:
                return True  # Restart from top-level
            elif old_path:
                path = old_path.pop()
                nested_directory -= 1
                continue
            else:
                continue

        try:
            num = int(choice)
        except ValueError:
            print(f'"{choice}" is not a valid number. Try again.')
            continue

        if num < 1 or num > len(dirs):  # Check valid selection
            print(f'"{num}" is out of range. Try again.')
            continue

        old_path.append(path)  # Drill into selected folder
        path = os.path.join(path, dirs[num - 1])

        await analyze(path, max_threads)
        nested_directory += 1
