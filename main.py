# Import necessary modules
import asyncio
import psutil
import install
from disk_analyzer import analyzer as base_analyzer
from disk_analyzer_optimize import analyzer as optimized_analyzer

#======================================================
# List all mounted disk drives
def list_drives():
    partitions = psutil.disk_partitions(all=False)
    return [p.device for p in partitions]

#======================================================
# Select drive: auto-select if one drive, else prompt user
def select_drive():
    drives = list_drives()
    if len(drives) == 1:
        return drives[0]
    for i, d in enumerate(drives, 1):
        print(f"{i}: {d}")
    while True:
        choice = input("Select drive: ")
        if choice.isdigit() and 1 <= int(choice) <= len(drives):
            return drives[int(choice) - 1]

#======================================================
# Handle drive selection when multiple drives exist
def input_case(drives):
    print("Multiple drives found. Select one or type 'exit' to quit.")
    while True:
        number = input()
        if number == "exit":
            exit()
        if number.isdigit() and 1 <= int(number) <= len(drives):
            return drives[int(number) - 1]
        else:
            print("Invalid drive. Try again.")

#======================================================
# Main async function to run the analyzer
async def main():
    restart = False
    drives = list_drives()

    for i, d in enumerate(drives):
        print(f"{i + 1}: {d}")
    
    path = "/" if len(drives) == 1 else input_case(drives)

    print("Select analyzer version: 1) Base 2) Optimized")
    choice = input("> ")
    
    if choice == "1":
        restart = base_analyzer.analyzer(path)  # Base analyzer (sync)
    elif choice == "2":
        print("Enter number of threads (default: 4):")
        try:
            max_threads = int(input("> "))
        except ValueError:
            max_threads = 4
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            loop.set_default_executor(executor)
            restart = await optimized_analyzer.analyzer(path, max_threads=max_threads)
    else:
        print("Invalid selection")
    
    if restart:
        await main()  # Restart scan if needed

#======================================================
# Entry point
if __name__ == "__main__":
    asyncio.run(main()
