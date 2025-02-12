import os
import subprocess
import sys
from utils import log_message, create_directory, fetch_runinfo

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
            sra_file = os.path.join(srr_output_dir, f"{srr_id}.sra")
            srr_csv_file = os.path.join(geo_dir, f"{geo_dir.split('/')[-1]}_SRR.csv")  # Adjust path as needed

            # Check if the SRR CSV file exists
            if os.path.exists(srr_csv_file):
                self._log_and_print(f"Skipping run info download for {srr_id}, {srr_csv_file} already exists.")
                continue

            # If the SRA file exists but the SRR CSV does not, fetch the run info
            if os.path.exists(sra_file):
                self._log_and_print(f"Building SRR list from metadata for {srr_id}...")
                gds_id = self.extract_gds_id(srr_id)  # Implement this method to extract GDS ID from SRR ID
                runinfo_file = fetch_runinfo(gds_id, geo_dir)  # Fetch run info
                srr_ids = self.extract_srr_ids_from_runinfo(runinfo_file)  # Implement this method to extract SRR IDs
            else:
                # Download the SRR file if it doesn't exist
                try:
                    prefetch_command = ["prefetch", srr_id, "-O", srr_output_dir]
                    subprocess.run(prefetch_command, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)
                    self._log_and_print(f"Successfully fetched {srr_id}.")
                except subprocess.CalledProcessError as e:
                    self._log_and_print(f"Error downloading {srr_id}: {e}", level="ERROR")
                    continue

    def extract_gds_id(self, srr_id: str) -> str:
        """Extract GDS ID from the SRR ID (implement this based on your logic)."""
        # Placeholder for actual implementation
        return "GDS_ID"

    def extract_srr_ids_from_runinfo(self, runinfo_file: str) -> list:
        """Extract SRR IDs from the run info file."""
        # Implement logic to read the run info file and extract SRR IDs
        return []

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
