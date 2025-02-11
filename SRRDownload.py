import os
import subprocess
import sys
from utils import log_message, create_directory

class SRRDownload:
    def __init__(self, base_dir: str):
        """
        Initialize the SRRDownload class with a base directory.
        """
        self.base_dir = base_dir

    def download_srrs(self, srr_ids: list, geo_dir: str) -> None:
        """
        Download SRR files using prefetch.
        """
        for srr_id in srr_ids:
            self._log_and_print(f"Fetching SRR {srr_id}...")
            srr_output_dir = create_directory(os.path.join(geo_dir, srr_id))

            try:
                prefetch_command = ["prefetch", srr_id, "-O", srr_output_dir]
                subprocess.run(prefetch_command, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)
                self._log_and_print(f"Successfully fetched {srr_id}.")

                sra_file = os.path.join(srr_output_dir, f"{srr_id}.sra")
                if not os.path.exists(sra_file):
                    self._log_and_print(f"Error: SRA file {sra_file} not found. Skipping {srr_id}.", level="ERROR")
            except subprocess.CalledProcessError as e:
                self._log_and_print(f"Error downloading {srr_id}: {e}", level="ERROR")
                continue

    def _log_and_print(self, message: str, level: str = "INFO") -> None:
        """
        Logs message and prints to stdout immediately for real-time SLURM visibility.
        """
        log_message(message, level)
        print(message, flush=True)

    def read_srr_ids(self, file_path: str) -> list:
        """Read SRR IDs from a file."""
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python SRRDownload.py <srr_ids_file> <base_dir>")
        sys.exit(1)
    
    srr_ids_file = sys.argv[1]
    base_dir = sys.argv[2]

    srr_downloader = SRRDownload(base_dir)
    
    srr_ids = srr_downloader.read_srr_ids(srr_ids_file)
    
    geo_dir = "your_geo_directory"  # Replace with actual geo directory path
    srr_downloader.download_srrs(srr_ids, geo_dir)
