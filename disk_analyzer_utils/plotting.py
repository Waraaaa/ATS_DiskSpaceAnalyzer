#======================================================
# Import
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from disk_analyzer_utils.utils import bytes_to_readable

#======================================================
# Plots disk usage data in paginated horizontal bar charts
def plot(data, base_path, page_size=20):

    data_sorted = sorted(data, key=lambda x: x["size"], reverse=True)  # Sort by size
    total_pages = math.ceil(len(data_sorted) / page_size)  # Calculate pages

    for page in range(total_pages):
        start = page * page_size
        end = start + page_size
        chunk = data_sorted[start:end]

        paths = [item["path"] for item in chunk]  # Get paths for this page
        sizes = [item["size"] for item in chunk]  # Get sizes for this page

        fig_height = max(5, 0.4 * len(chunk))  # Adjust height based on number of bars
        fig, ax = plt.subplots(figsize=(12, fig_height))

        bars = ax.barh(paths, sizes, color='skyblue')  # Horizontal bar chart
        ax.invert_yaxis()  # Largest items on top

        ax.set_xlabel("Size")  # X-axis label
        ax.set_title(f"Disk Usage ({base_path}) — Page {page + 1}/{total_pages}")  # Title

        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: bytes_to_readable(x))  # Format x-axis to human-readable
        )

        for bar, size in zip(bars, sizes):  # Annotate each bar
            ax.text(
                bar.get_width() + bar.get_width() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                bytes_to_readable(size),
                va='center'
            )

        plt.tight_layout()  # Adjust layout
        plt.grid(axis='x', linestyle='--', alpha=0.6)  # Add grid

        plt.show(block=False)  # Display chart
        print(f"\nShowing page {page + 1} of {total_pages}.")

        if page < total_pages - 1:
            input("Press Enter to show next page...")
            plt.close(fig)
        else:
            print("Last page. Close the plot window manually to finish.")
